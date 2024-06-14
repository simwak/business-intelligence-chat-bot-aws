import streamlit as st
import pandas as pd
import pydeck as pdk
import ast
from llm import chatCompletion
from io import StringIO
import streamlit_authenticator as stauth

def writeMap(content):
  try:
    chartData = content["data"]
    zoomLevel = content["zoomLevel"]

    df = pd.read_csv(StringIO(chartData), sep=",", header=[0])

    initialIndex = 0
    layers = []

    if "value" in df:
      # Calculate radius
      highestValue = df["value"].max()
      highestRadius = 800
      lowestRadius = 50

      df["radius"] = df["value"].apply(lambda value: max(lowestRadius, value / highestValue * highestRadius))

      # Get initial view state location
      initialIndex = df.idxmax()["value"]

      # Set layers
      layers = [
        pdk.Layer(
          'ScatterplotLayer',
          data=df,
          get_position='[lon, lat]',
          get_color='[200, 30, 0, 160]',
          get_radius="radius",
          radius_scale=100,
        ),
      ] 
    else:
      icon_data = {
        # This file is from the Open Clip Art Library, which released it explicitly into the public domain.
        # https://openclipart.org/detail/262009/map-pin-2 - https://openclipart.org/share
        "url": "https://openclipart.org/image/400px/262009",
        "width": 229,
        "height": 400,
        "anchorY": 400,
      }     

      df["icon_data"] = None
      for i in df.index:
        df["icon_data"][i] = icon_data

      layers = [
        pdk.Layer(
          type="IconLayer",
          data=df,
          get_icon="icon_data",
          get_size=4,
          size_scale=15,
          get_position=["lon", "lat"],
          pickable=True,
        ),
      ] 

    print(df)

    st.pydeck_chart(pdk.Deck(
      map_style=None,
      initial_view_state=pdk.ViewState(
        latitude=df['lat'].values[initialIndex],
        longitude=df['lon'].values[initialIndex],
        zoom=zoomLevel,
        pitch=50,
      ),
      layers=layers,
    ))
  except Exception as e:
    print(e)
    st.chat_message("assistant").warning("Sorry, there was an error rendering this map: " + repr(e) + ": " + str(e))

def writeChart(content):
  try:
    chartType = content["chart_type"]
    chartData = content["data"]

    df = pd.read_csv(StringIO(chartData), sep=",", header=[0])
    print(df)

    # Capitalize Label
    xHeader = list(df)[0].replace("_", " ").capitalize()
    yHeader = list(df)[1].replace("_", " ").capitalize()

    df = df.rename(columns={list(df)[0]: xHeader, list(df)[1]: yHeader})

    match chartType:
      case "bar":
        st.bar_chart(df, x=xHeader, y=yHeader)
      case "area":
        st.area_chart(df, x=xHeader, y=yHeader)
      case "line":
        st.line_chart(df, x=xHeader, y=yHeader)
      case "scatter":
        st.scatter_chart(df, x=xHeader, y=yHeader)
  except Exception as e:
    print(e)
    st.chat_message("assistant").warning("Sorry, there was an error rendering this chart (" + repr(e) + ": " + str(e))

def writeMessage(msg):
  # User & Tools
  if msg["role"] == "user":
    for c in msg["content"]:
      if c["type"] == "text":
        st.chat_message("user").write(c["text"])

      if c["type"] == "tool_result":
        if c["content"].startswith("Error"):
          # st.chat_message("assistant").warning(msg["content"])
          return

        try:
          content = ast.literal_eval(c["content"])
          if "content_type" not in content:
            raise Exception()
        except:
          pass
        else:
          if content["content_type"] == "map":
            writeMap(content)
          elif content["content_type"] == "chart":
            writeChart(content)

  # Assistant
  if msg["role"] == "assistant" and ("stop_reason" not in msg or msg["stop_reason"] != "tool_use"):
    for c in msg["content"]:
      if c["type"] == "text":
        st.chat_message("assistant").write(c["text"])

title = "📊 Data Analyst"
st.set_page_config(page_title=title)
st.title(title) 

if "messages" not in st.session_state:
  st.session_state["messages"] = [
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "Hello! How can I assist you today?"
        }
      ]
    }
  ]

for msg in st.session_state.messages:
    writeMessage(msg)

if prompt := st.chat_input():
  st.session_state.messages.append({
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": prompt
      }
    ]
  })
  st.chat_message("user").write(prompt)
  
  responses = chatCompletion(st.session_state.messages)
  
  for msg in responses:
    writeMessage(msg)
