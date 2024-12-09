from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import xmlrpc.client
from .models import DatosExternos, TipoTeja, Viaticos, Ubicacion, Estudio_conexion
from django.http import JsonResponse


def home(request):

    # Obtener DatosExternos
    datos_externos = DatosExternos.objects.first()
    if datos_externos:
        hsp = datos_externos.hsp
        security_factor = datos_externos.security_factor
        imprevistos = datos_externos.imprevistos
        material_electrico = datos_externos.material_electrico
        certificacion_retie_v1 = datos_externos.certificacion_retie_v1
        certificacion_retie_v2 = datos_externos.certificacion_retie_v2


    else:
        # Si no hay datos, asignar valores por defecto
        hsp = 0
        security_factor = 0
        imprevistos = 0
        material_electrico = 0
        certificacion_retie_v1 = 0
        certificacion_retie_v2 = 0

    datos_externos_dict = {
        'hsp': hsp,
        'security_factor': security_factor,
        'imprevistos': imprevistos,
        'material_electrico': material_electrico,
        'certificacion_retie_v1': certificacion_retie_v1,
        'certificacion_retie_v2': certificacion_retie_v2,
        'pct_iva': datos_externos.pct_iva if datos_externos else 0,
        'pct_instalacion': datos_externos.pct_instalacion if datos_externos else 0,
        'consultoria_tributaria': datos_externos.consultoria_tributaria if datos_externos else 0,
        'proteccionCNO': datos_externos.proteccionCNO if datos_externos else 0
    }

    # Obtener datos de tejas de la base de datos
    tejas_data = get_tejas()

    #Cargar estudios de conexión
    estudio_conexion_data = get_estudio_conexion()

    # obtener datos de odoo
    paneles, inversores = connectin_oddo()

    #  Pasar los datos necesarios a la plantilla
    paneles_data = []
    for panel in paneles: 
        panel_id = panel['id']
        panel_name = panel['display_name']
        panel_power = panel['nominal_power']
        panel_area_in_cm = (panel['module_length'] * panel['module_width']) / 10 
        panel_sales_count = panel['sales_count']
        panel_price = panel['list_price']
        paneles_data.append({'id': panel_id, 'name': panel_name, 'power': panel_power, 'panel_area_in_cm': panel_area_in_cm, 'sales_count': panel_sales_count, 'panel_price': panel_price})
    inversores_data = []
    for inversor in inversores:
        inversor_id = inversor['id']
        inversor_name = inversor['display_name']
        inversor_power = inversor['input_dc']
        inversor_sales_count = inversor['sales_count']
        inversor_price = inversor['list_price']
        inversores_data.append({'id': inversor_id, 'name': inversor_name, 'power': inversor_power, 'inversor_price': inversor_price, 'sales_count': inversor_sales_count})

    # Convertir a JSON
    tejas_data = json.dumps(tejas_data)
    paneles_data = json.dumps(paneles_data)
    inversores_data = json.dumps(inversores_data)
    datos_externos_data = json.dumps(datos_externos_dict)
    estudio_conexion_data = json.dumps(estudio_conexion_data)

    return render(request, 'core/home.html', {'paneles': paneles_data, 'inversores': inversores_data, 'tejas': tejas_data, 'datos_externos': datos_externos_data, 'estudios_conexion': estudio_conexion_data})


def get_viaticos(request):
    try:
        viaticos = Viaticos.objects.first()
        if viaticos:
            viaticos_data = {
                'precio_hospedaje': float(viaticos.precio_hospedaje),
                'precio_viaticos': float(viaticos.precio_viaticos)
            }
        else:
            viaticos_data = {
                'precio_hospedaje': 0,
                'precio_viaticos': 0
            }
        return JsonResponse(viaticos_data)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'precio_hospedaje': 0,
            'precio_viaticos': 0
        }, status=500)
    
def get_estudio_conexion():
    try:
         # Obtener datos de estudio de conexión de la base de datos
        estudio_conexion = Estudio_conexion.objects.all()
        estudio_conexion_data = [{'id': ec.id, 'nombre': ec.nombre, 'precio': float(ec.precio)}
                     for ec in estudio_conexion]
        return estudio_conexion_data
    
    except Exception as e:

        return JsonResponse({
            'error': str(e),
            'id': 0,
            'nombre': "No hay datos disponibles",
            'precio': 0
        }, status=500)

def get_locations(request):
    locations = Ubicacion.objects.all()
    locations_data = [{'id': loc.id, 'nombre': loc.nombre, 'km_desde_medellin': loc.km_desde_medellin} 
                     for loc in locations]
    return JsonResponse(locations_data, safe=False)

def get_tejas():
    try:
        tejas = TipoTeja.objects.all()
        tejas_data = [{'id': teja.id, 'nombre': teja.nombre, 'precio_antes_de_iva': float(teja.precio_antes_de_iva)}
                      for teja in tejas]
        return tejas_data
    
    # return tejas_data
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'id': 0,
            'nombre': "No hay datos disponibles",
            'precio_antes_de_iva': 0
        }, status=500)


@csrf_exempt  # Solo para desarrollo, en producción maneja el CSRF apropiadamente
def submit_form(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Aquí procesarías los datos como necesites
            # Por ejemplo, guardarlos en la base de datos
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def connectin_oddo():

    db = 'hersic'
    password ='123456'
    username ='lider-ia@boost.net.co'
    url = 'https://hersic.tacticaweb.com.co/'
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format('https://hersic.tacticaweb.com.co/'))
    common.version()
    uid = common.authenticate(db,username,password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    paneles, inversores = get_odoo_data(models, db, uid, password)
    
    return paneles, inversores
    

def get_odoo_data(models, db, uid, password):
    
    paneles_ids = models.execute_kw(db, uid, password,
        'product.template', 'search',
        [[['nominal_power', '>', 0]]])
    paneles =  models.execute_kw(db, uid, password,
        'product.template', 'read',
        [paneles_ids])
    
    inversor_ids = models.execute_kw(db, uid, password,
        'product.template', 'search',
        [[['input_dc', '>', 0]]])
    inversores = models.execute_kw(db, uid, password,
        'product.template', 'read',
        [inversor_ids])

    return (paneles, inversores)
