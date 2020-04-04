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
  pais['Casos nuevos'] = pais['Casos'].diff()
  pais['Muertes nuevas'] = pais['Muertes'].diff()
  pais['Recuperados nuevos'] = pais['Recuperados'].diff()
  pais['Fecha'] = pais.index
  pais['Dia'] = pais['Fecha'].rank()
  pais['Pais'] = clave
  pais = pd.merge(pais, pob, left_on='Pais', right_on='alfa3')
  return(pais)


url_base = 'https://covidapi.info/api/v1/country/'
opciones = [
  {'label':u'México', 'value':'MEX'},
  {'label':'Estados Unidos', 'value':'USA'},
  {'label':'Argentina', 'value':'ARG'},
  {'label':'Brasil', 'value':'BRA'},
  {'label':'Chile', 'value':'CHL'},
  {'label':'Colombia' , 'value':'COL'},
  {'label':u'España', 'value':'ESP'},
  {'label':'Italia', 'value':'ITA'},
  {'label':'Reino Unido' , 'value':'GBR'}
]

pob = pd.read_csv('poblacion.csv')[['alfa3', 'pob_cienmiles']]

metricas_nom = [
  'Casos', 'Muertes', 'Recuperados', 
  'Casos nuevos', 'Muertes nuevas', 'Recuperados nuevos'
] 

metricas = [{'label':i, 'value':i} for i in metricas_nom]


paises = pd.concat([crear_df(i['value'], pob) for  i in opciones])
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
          placeholder=u'Elige un país',
          options=opciones, 
          value=['MEX', 'ARG', 'CHL'],
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
      dcc.Graph(id='plot-principal', className='plot'),
      dcc.Graph(id='plot-cienmiles', className='plot')
    ],
    className='holder'
    ),
    
    html.Div([
      html.P('Fuente de datos: '),
      html.A('2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE', 
        href='https://github.com/CSSEGISandData/COVID-19'),
      html.P(' (actualizado diariamente).'),
      html.Br(),
      html.P('Datos extaidos a través de '),
      html.A('CovidAPI', href = 'https://covidapi.info/'),
      html.P('.'),
      html.Br(),
      html.A('Repositorio en Github.', href='https://github.com/jboscomendoza/dashboard-covid-19')
    ],
    className='holder')
    
    
  ],
  className='holder'
)


def crear_traces(fechas, claves, metrica, escienmiles):
  traces=[]
  
  
  for i in claves: 
    paises_df = paises[paises['Dia'].between(fechas[0], fechas[1])]
    paises_df = paises_df[paises_df['Pais'].isin([i])]
      
    if escienmiles:
      paises_df[metrica] = paises_df[metrica] / paises_df['pob_cienmiles'].unique()
      paises_df[metrica] = round(paises_df[metrica], 2)
      nombre = i + ' por cien mil habitantes'
    
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
  traces=crear_traces(fechas, claves, metrica, escienmiles=False)
  cuerpo={'data': traces, 'layout':{'title': metrica + ' totales'}}
  return cuerpo


@app.callback(
    Output('plot-cienmiles', 'figure'),
  [
    Input('fecha-slider', 'value'),
    Input('paises-drop', 'value'),
    Input('metrica-drop', 'value')
  ]  
)
def update_cliente(fechas, claves, metrica):
  traces=crear_traces(fechas, claves, metrica, escienmiles=True)
  cuerpo={'data': traces, 'layout':{'title': metrica + ' por cien mil habitantes'}}
  return cuerpo



if __name__ == '__main__':
    app.run_server(debug=True)
