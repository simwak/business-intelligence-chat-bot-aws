import os
import os.path
import json
import redshift_connector
import pandas
import geopy

import boto3

chatCompletionLimit = 20
queryRowLimit = 100
mapEntryLimit = 100
modelId = "anthropic.claude-3-haiku-20240307-v1:0" # "anthropic.claude-3-haiku-20240307-v1:0", "anthropic.claude-3-opus-20240229-v1:0", "anthropic.claude-3-sonnet-20240229-v1:0" 

systemMessage = open("system-message.md", "r").read().replace("$queryRowLimit", str(queryRowLimit))
tools = [
  {
    "name": "getDatabases",
    "description": "Gets all accessible databases as a list",
    "input_schema": {
      "type": "object",
    }
  },
  {
    "name": "getDatabaseSchema",
    "description": "Gets the schema for a database",
    "input_schema": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "Name of the database you want to receive the schema for",
        },
      },
      "required": ["name"]
    }
  },
  {
    "name": "executeQuery",
    "description": "Executes a SQL query against the data warehouse",
    "input_schema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The full SQL query. Always end your SQL query with 'LIMIT " + str(queryRowLimit) + "'",
        },
      },
      "required": ["query"]
    }
  },
  {
    "name": "chart",
    "description": "Shows a chart to the user above",
    "input_schema": {
      "type": "object",
      "properties": {
        "chart_type": {
          "type": "string",
          "enum": ["bar", "area", "line", "scatter"],
          "description": "The type of the chart",
        },
        "data": {
          "type": "string",
          "description": "Data of the chart represented as CSV. Data must be in a format, that it makes sense for the given chart type. The first column is the x-axis, the second one the y-axis. Always include a header.",
        }
      },
      "required": ["chart_type", "data"],
    }
  },
  {
    "name": "map",
    "description": "Shows a map to the user above",
    "input_schema": {
      "type": "object",
      "properties": {
        "rows": {
          "type": "array",
          "description": "All entries to show on the map",
          "items": {
            "type": "object",
            "properties": {
              "country": {
                "type": "string",
                "description": "Country of the location displayed on the map"
              },
              "state": {
                "type": "string"
              },
              "city": {
                "type": "string"
              },
              "zip_code": {
                "type": "string"
              },
              "street": {
                "type": "string"
              },
              "lat": {
                "type": "number",
                "description": "Latitude of the map entry if known. If empty, the latitude will be retrieved by external API"
              },
              "lon": {
                "type": "number",
                "description": "Longitude of the map entry if known, the longitude will be retrieved by external API"
              },
              "value": {
                "description": "Optional value to be shown on the map"
              },
            },
            "required": ["country"]
          }
        },
        "zoomLevel": {
          "type": "number",
          "description": "Given on the data, choose a zoom level between 1 and 20 where 20 is on street level and 1 on world level.",
        },
      },
      "required": ["data", "zoomLevel"],
    }
  }
]
bedrockClient = boto3.client("bedrock-runtime", region_name="us-west-2")

def getDatabases():
  # Hardcoded in this prototype
  exampleDatabase = {
    "name": "example-database",
    "description": "A database of our web shop in Brazil"
  }

  return [ exampleDatabase ]

def getDatabaseSchema(args):
  path = 'schemas/{}.sql'.format(args["name"])

  if os.path.isfile(path):
    f = open(path, "r")
    return f.read()
  else:
    return "Error: not found"

def executeQuery(args):
  host = os.getenv("DW_HOST")
  user = os.getenv("DW_USER")
  password = os.getenv("DW_PASSWORD")
  database = os.getenv("DW_DATABASE")
  
  try:
    conn = redshift_connector.connect(
      host=host,
      database=database,
      user=user,
      password=password
    )

    # if not args["query"].endswith('LIMIT ' + str(queryRowLimit)):
    #   return "Error: Query is not limited by " + str(queryRowLimit) + " (LIMIT " + str(queryRowLimit) + " at the end)"

    cursor: redshift_connector.Cursor = conn.cursor()
    cursor.execute(args["query"])

    return cursor.fetchall()
  except Exception as e:
    return "Error: " + repr(e) + " " + str(e)

def chart(args):
  chartType = args["chart_type"] # bar, area, line, scatter
  chartData = args["data"] # csv

  return {
    "content_type": "chart",
    "chart_type": chartType,
    "data": chartData,
  }

def map(args):
  zoomLevel = args["zoomLevel"] # 1-20 (20 = Street, 1 = World)
  rows = args["rows"]

  if len(rows) > mapEntryLimit:
    return "Error: Too many entries. Only " +  str(mapEntryLimit) + " are allowed."

  # Setup client
  API_KEY = os.getenv("BING_MAPS_API_KEY")
  geolocator = geopy.geocoders.Bing(API_KEY)

  for row in rows:
    if not ("lat" in row and "lon" in row):
      query = ""

      if "street" in row:
        query += str(row["street"]) + ", "

      if "zip_code" in row:
        query += str(row["zip_code"]) + ", "

      if "city" in row:
        query += str(row["city"]) + ", "

      if "state" in row:
        query += str(row["state"]) + ", "

      query += str(row["country"])

      try:
        client = boto3.client('location', region_name="eu-central-1")
        response = client.search_place_index_for_text(IndexName="demo",Text=query)

        row["lat"] = response['Results'][0]['Place']['Geometry']['Point'][1]
        row["lon"] = response['Results'][0]['Place']['Geometry']['Point'][0]
      except Exception as error:
        print(error)
        return "Failed to get location for: " + query + " with error " + error

  df = pandas.DataFrame(rows)

  return {
    "content_type": "map",
    "data": df.to_csv(index=False),
    "zoomLevel": zoomLevel,
  }

def chatCompletion(messages):
  chatCompletions = 0
  responses = [] # Delta to messages

  print(messages)

  while True:
    if messages[-1]["role"] == "assistant" or chatCompletions > chatCompletionLimit:
      break

    response = bedrockClient.invoke_model(
      body = json.dumps(
        {
          "anthropic_version": "bedrock-2023-05-31",
          "max_tokens": 100000,
          "system": systemMessage,
          "messages": bedrockMessageFormat(messages[1:]),
          "tools": tools
        }  
      ),
      modelId = modelId,
      accept = "application/json",
      contentType = "application/json"
    )

    body = json.loads(response['body'].read())
    responses.append(body)
    messages.append(body)
    print(body)

    for c in body["content"]:
      if c["type"] == 'tool_use':
        try:
          toolFunction = globals()[c['name']]
          value = ""
          args = c['input']
          
          print("Calling function " + c['name'])

          if args is not None and len(args) > 0:
            value = str(toolFunction(args))
          else: 
            value = str(toolFunction())

          toolContent = value
        except Exception as e:
          toolContent = "Error: Function call failed: " + repr(e) + ": " + str(e)
        finally:
          toolMessage = {
            "role": "user",
            "content": [
              {
                "type": "tool_result",
                "tool_use_id": c["id"],
                "content": toolContent
              },
            ]
          }

          messages.append(toolMessage)
          responses.append(toolMessage)
          print(toolMessage)
    
    chatCompletions += 1

  return responses

def bedrockMessageFormat(messages):
  bedrockMessages = []

  for m in messages:
    bedrockMessages.append({
      "role": m['role'],
      "content": m['content']
    })
  
  return bedrockMessages