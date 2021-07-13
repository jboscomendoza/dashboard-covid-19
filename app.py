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
app.title = u'Métricas de COVID-19'


requests_cache.install_cache(cache_name='covid_api', backend='sqlite', expire_after=3600)


def crear_df(clave, pob):
  pais_json = requests.get(url_base + clave).json()
  pais = pd.DataFrame.from_dict(pais_json['result'], orient='index')
  pais = pais.rename(columns={'confirmed':'Casos', 'deaths':'Muertes', 'recovered':'Recuperados'})
  pais = pais[pais['Casos'] > 0]
  pais[['Casos nuevos', 'Muertes nuevas', 'Recuperados nuevos']] = pais[['Casos', 'Muertes', 'Recuperados']].diff()
  pais['Casos nuevos']     = pais['Casos nuevos'].rolling(5).mean()
  pais['Muertes nuevas']     = pais['Muertes nuevas'].rolling(5).mean()
  pais.loc[pais['Recuperados nuevos'] < 0, 'Recuperados nuevos'] = 0
  pais['Recuperados nuevos'] = pais['Recuperados nuevos'].rolling(5).mean()
  pais['Fecha'] = pais.index
  pais['Dia'] = pais['Fecha'].rank()
  pais['Pais'] = clave
  pais = pd.merge(pais, pob, left_on='Pais', right_on='alfa3')
  return(pais)


url_base = 'https://covidapi.info/api/v1/country/'
opciones = [
  {'label':u'Argentina', 'value':'ARG'},
  {'label':u'Brasil', 'value':'BRA'},
  {'label':u'Chile', 'value':'CHL'},
  {'label':u'Canadá', 'value':'CAN'},
  {'label':u'Colombia', 'value':'COL'},
  {'label':u'Ecuador', 'value':'ECU'},
  {'label':u'España', 'value':'ESP'},
  {'label':u'Estados Unidos', 'value':'USA'},
  {'label':u'Italia', 'value':'ITA'},
  {'label':u'Japón', 'value':'JPN'},
  {'label':u'México', 'value':'MEX'},
  {'label':u'Reino Unido', 'value':'GBR'}
]


pob = pd.read_csv('poblacion.csv')[['alfa3', 'pob_cienmiles']]


# metricas_nom = [
#   'Casos', 'Muertes', 'Recuperados', 
#   'Casos nuevos', 'Muertes nuevas', 'Recuperados nuevos'
# ] 
# metricas = [{'label':i, 'value':i} for i in metricas_nom]

metricas = [
    {'label': 'Casos', 'value': 'Casos'},
    {'label': 'Muertes', 'value': 'Muertes'},
    {'label': 'Recuperados', 'value': 'Recuperados'},
    {'label': u'Casos nuevos (Promedio cinco últimos días)', 'value': 'Casos nuevos'},
    {'label': u'Muertes nuevas (Promedio cinco últimos días)', 'value': 'Muertes nuevas'},
    {'label': u'Recuperados nuevos (Promedio cinco últimos días)', 'value': 'Recuperados nuevos'},
]


paises = pd.concat([crear_df(i['value'], pob) for i in opciones])


app.layout = html.Div([
  html.Div([
    html.H1(children='Métricas de COVID-19 ', className='titulo'),
  ],
  className='holder'),  
    
  html.Div([
    html.Div([
      html.H3(children = 'Filtrar por país'),
      dcc.Dropdown(
        id='paises-drop',
        placeholder=u'Elige un país',
        options=opciones, 
        value=['MEX', 'ARG', 'CHL'],
        multi=True
      )
    ], 
    className='hold-drops'
    ),
  
    html.Div([
      html.H3(children = 'Filtrar por métrica'),
      dcc.Dropdown(
        id='metrica-drop',
        options=metricas,
        value='Casos',
        clearable=False
      ),
    ],
    className='hold-drops'
    ),
    
    html.Div([
      html.H3('Filtrar por tipo de periodo'),
      dcc.Dropdown(
        id='periodo-drop',
        options=[
          {'label':'Días desde el primer caso', 'value':'Dia'},
          {'label':'Fecha', 'value':'Fecha'}
        ],
        value='Fecha',
        clearable=False
      ),
    ],
    className='hold-drops'
    )
    
    
  ],
  className='holder'
  ),
    
  html.Div([
    dcc.Graph(id='plot-principal', className='plot'),
    dcc.Graph(id='plot-cienmiles', className='plot')
  ],
  className='holder'
  ),
    
  html.Div([
    dcc.Markdown(u'''
    Fuente de datos: [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE] (https://github.com/CSSEGISandData/COVID-19) (actualizado diariamente).
    
    Datos extraídos a través de [CovidAPI](https://covidapi.info/).
    
    Repositorio de Github: [jboscomendoza/dashboard-covid-19](https://github.com/jboscomendoza/dashboard-covid-19).
    ''')
  ],
  className='holder'
  )

  ],
  className='holder'
)


def crear_traces(claves, metrica, periodo, escienmiles):
  traces=[]

  for i in claves: 
    paises_df = paises[paises['Pais'].isin([i])]
      
    if escienmiles:
      paises_df[metrica] = paises_df[metrica] / paises_df['pob_cienmiles'].unique()
      paises_df[metrica] = round(paises_df[metrica], 2)
      nombre = i + ' por cien mil habitantes'
    
    parte = {'x':paises_df[periodo], 'y':paises_df[metrica], 'mode': 'lines-markers', 'name':i}
    traces.append(parte)
  
  return traces


# Plot total
@app.callback(
  Output('plot-principal', 'figure'),
  [
    Input('paises-drop', 'value'),
    Input('metrica-drop', 'value'),
    Input('periodo-drop', 'value')
  ]  
)
def update_cliente(claves, metrica, periodo):
  traces=crear_traces(claves, metrica, periodo, escienmiles=False)
  cuerpo={'data': traces, 'layout':{'title': metrica + ' totales', 'xaxis':{'title':periodo}}}
  return cuerpo


# Plot por cien mil
@app.callback(
    Output('plot-cienmiles', 'figure'),
  [
    Input('paises-drop', 'value'),
    Input('metrica-drop', 'value'),
    Input('periodo-drop', 'value')
  ]  
)
def update_cliente(claves, metrica, periodo):
  traces=crear_traces(claves, metrica, periodo, escienmiles=True)
  cuerpo={'data': traces, 'layout':{'title': metrica + ' por cien mil habitantes', 'xaxis':{'title':periodo}}}
  return cuerpo


if __name__ == '__main__':
    app.run_server(debug=True)
