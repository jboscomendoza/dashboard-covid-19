# -*- coding: utf-8 -*-
import dash
import requests
import requests_cache
import pandas as pd
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


requests_cache.install_cache(cache_name='covid_api', backend='sqlite', expire_after=3600)


def crear_df(clave):
  pais_json = requests.get(url_base + clave).json()
  pais = pd.DataFrame.from_dict(pais_json['result'], orient='index')
  pais = pais.rename(columns={'confirmed':'Casos', 'deaths':'Muertes', 'recovered':'Recuperados'})
  pais = pais[pais['Casos'] > 0]
  pais['Fecha'] = pais.index
  pais['Dia'] = pais['Fecha'].rank()
  pais['Pais'] = clave
  return(pais)


url_base = 'https://covidapi.info/api/v1/country/'
opciones = [
  {'label': u'México', 'value': 'MEX'},
  {'label': 'Estados Unidos', 'value': 'USA'},
  {'label': 'Argentina', 'value': 'ARG'},
  {'label': 'Italia', 'value': 'ITA'},
  {'label': u'España', 'value': 'ESP'}
]

metricas = [{'label':i, 'value':i} for i in ['Casos', 'Muertes', 'Recuperados']]

paises = pd.concat([crear_df(i['value']) for  i in opciones])
dia_min = int(paises['Dia'].min())
dia_max = int(paises['Dia'].max())
marcas = {i:str(i) for i in range(10, dia_max, 10)}
marcas.update([(1, '1'), (dia_max, str(dia_max))])

app.layout = html.Div([
    html.Div([
      html.H1(children='Métricas de COVID-19 ', className='titulo'),
    ],
    className='holder'),  
    
    html.Div([
      html.Div([
        html.H4(children = 'Filtrar por país'),
        dcc.Dropdown(
          id='paises-drop',
          options=opciones,
          value=['MEX'],
          multi=True
        )], 
      className='hold-drops'
      ),
  
      html.Div([
        html.H4(children = 'Filtrar por métrica'),
        dcc.Dropdown(
          id='metrica-drop',
          options=metricas,
          value='Casos',
        )
      ],
      className='hold-drops'
      ),
    ],
    className='holder'
    ),

    html.Div([
      html.H4(children=u'Dias desde el primer caso confirmado'),
      dcc.RangeSlider(
        id='fecha-slider',
        min=dia_min,
        max=dia_max,
        value=[dia_min, dia_max],
        step=1,
        updatemode='drag',
        marks=marcas,
        className='slider'
      )
    ],
    className='holder'
    ),
    
    html.Div([
      dcc.Graph(id='plot-principal', className='plot')
    ],
    className='holder'
    ),
  ],
  className='holder'
)


def crear_traces(fechas, claves, metrica):
  traces=[]
  
  for i in claves: 
    paises_df = paises[paises['Dia'].between(fechas[0], fechas[1])]
    paises_df = paises_df[paises_df['Pais'].isin([i])]
    parte = {'x':paises_df['Dia'], 'y':paises_df[metrica], 'mode': 'lines-markers', 'name':i}
    traces.append(parte)
  
  return traces


# Plot
@app.callback(
    Output('plot-principal', 'figure'),
  [
    Input('fecha-slider', 'value'),
    Input('paises-drop', 'value'),
    Input('metrica-drop', 'value')
  ]  
)
def update_cliente(fechas, claves, metrica):
  traces=crear_traces(fechas, claves, metrica)
  cuerpo={'data': traces, 'layout':{'title': metrica}}
  return cuerpo


if __name__ == '__main__':
    app.run_server(debug=True)
