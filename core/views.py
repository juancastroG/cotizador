from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import xmlrpc.client
from .models import DatosExternos, TipoTeja, Viaticos, Ubicacion

def home(request):

    # Obtener DatosExternos
    datos_externos = DatosExternos.objects.first()
    if datos_externos:
        hsp = datos_externos.hsp
        security_factor = datos_externos.security_factor
        imprevistos = datos_externos.imprevistos
        material_electrico = datos_externos.material_electrico
        certificacion_retie = datos_externos.certificacion_retie

    else:
        # Si no hay datos, asignar valores por defecto
        hsp = 0
        security_factor = 0
        imprevistos = 0
        material_electrico = 0
        certificacion_retie = 0

    datos_externos_dict = {
        'hsp': hsp,
        'security_factor': security_factor,
        'imprevistos': imprevistos,
        'material_electrico': material_electrico,
        'certificacion_retie': certificacion_retie
    }

    # Obtener datos de tejas de la base de datos
    tejas = TipoTeja.objects.all()
    tejas_data = []

    
    # Convertir la URL de la imagen a string para JSON
    for teja in tejas:
        teja_dict = {
            'id': teja.id,
            'nombre': teja.nombre,
            'precio_antes_de_iva': float(teja.precio_antes_de_iva),
            'imagen': request.build_absolute_uri(teja.imagen.url) if teja.imagen else ''
        }
        tejas_data.append(teja_dict)

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
        inversores_data.append({'id': inversor_id, 'name': inversor_name, 'power': inversor_power})

    # Convertir a JSON
    tejas_data = json.dumps(tejas_data)
    paneles_data = json.dumps(paneles_data)
    inversores_data = json.dumps(inversores_data)
    datos_externos_data = json.dumps(datos_externos_dict)

    return render(request, 'core/home.html', {'paneles': paneles_data, 'inversores': inversores_data, 'tejas': tejas_data, 'datos_externos': datos_externos_data})


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
