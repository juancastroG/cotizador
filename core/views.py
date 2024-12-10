from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import xmlrpc.client
from .models import DatosExternos, TipoTeja, Viaticos, Ubicacion, Estudio_conexion
from django.http import JsonResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.colors import Color
from decimal import Decimal
from django.http import HttpResponse

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
        estudio_conexion_data = [{'id': ec.id, 'nombre': ec.nombre, 'precio': float(ec.precio), 'desde': float(ec.since), 'hasta': float(ec.until)}
                     for ec in estudio_conexion]
        return estudio_conexion_data
    
    except Exception as e:

        return JsonResponse({
            'error': str(e),
            'id': 0,
            'nombre': "No hay datos disponibles",
            'precio': 0,
            'desde': 0,
            'hasta': 0
        }, status=500)

def get_locations(request):
    locations = Ubicacion.objects.all()
    locations_data = [{'id': loc.id, 'nombre': loc.nombre, 'km_desde_medellin': loc.km_desde_medellin} 
                     for loc in locations]
    return JsonResponse(locations_data, safe=False)

def get_tejas():
    try:
        tejas = TipoTeja.objects.all()
        tejas_data = [{'id': teja.id, 'nombre': teja.nombre, 'precio_antes_de_iva': float(teja.precio_antes_de_iva), 'imagen': teja.imagen.url}
                      for teja in tejas]
        return tejas_data
    
    # return tejas_data
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'id': 0,
            'nombre': "No hay datos disponibles",
            'precio_antes_de_iva': 0,
            'imagen': "No hay datos disponibles"
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


#Reporte pdf
# Definimos los colores de la paleta
VERDE_CLOROFILA = Color(0.039, 0.239, 0.200)  # #0a3d33
PINO_OSCURO = Color(0.102, 0.318, 0.267)      # #1a512e
ESMERALDA_VIVO = Color(0.227, 0.655, 0.208)   # #3aa735
CYAN_PROFUNDO = Color(0.000, 0.529, 0.463)    # #008776

def format_currency(amount):
    """Formatea números a formato de moneda"""
    try:
        if isinstance(amount, str):
            # Remover el símbolo de peso y las comas
            amount = amount.replace('$', '').replace(',', '').strip()
            if not amount:
                return "$0.00"
        return "${:,.2f}".format(float(amount))
    except (ValueError, TypeError):
        return "$0.00"

def generate_pdf(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Crear el documento PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Cotizacion-{data["fullName"]}.pdf"'
            
            doc = SimpleDocTemplate(
                response,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Contenedor para los elementos del PDF
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=VERDE_CLOROFILA,
                spaceAfter=30,
                alignment=1  # Centrado
            ))
            
            # Título
            elements.append(Paragraph(
                "Cotización Sistema Solar",
                styles['CustomTitle']
            ))
            
            # Información del cliente
            elements.append(Paragraph(
                f"Cliente: {data['fullName']}",
                styles['Heading2']
            ))
            elements.append(Spacer(1, 12))
            
            # Detalles del sistema
            system_info = [
                ['Concepto', 'Valor'],
                ['Consumo mensual', f"{data['consumption']} kWh"],
                ['Costo por kWh', format_currency(data['costPerKwh'])],
                ['Área disponible', f"{data['availableArea']} m²"],
                ['Transformador', f"{data['transformer']} kVA"],
            ]
            
            # Crear tabla de información del sistema
            system_table = Table(system_info, colWidths=[4*inch, 2*inch])
            system_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), CYAN_PROFUNDO),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, VERDE_CLOROFILA),
            ]))
            elements.append(system_table)
            elements.append(Spacer(1, 20))
            
            # Resumen de costos
            cost_items = [
                ['Componente', 'Costo'],
                ['Panel(es)', format_currency(data['costSummary'].get('Costo panel(es)', 0))],
                ['Inversor(es)', format_currency(data['costSummary'].get('Costo inversor (es)', 0))],
                ['ExportManager', format_currency(data['costSummary'].get('Costo ExportManager', 0))],
                ['CTSolis', format_currency(data['costSummary'].get('Costo de CTSolis', 0))],
                ['Protector(es) inversor(es)', format_currency(data['costSummary'].get('Costo de protector(es) inversor(es)', 0))],
                ['Teja', format_currency(data['costSummary'].get('Teja', 0))],
                ['Material eléctrico', format_currency(data['costSummary'].get('Material eléctrico', 0))],
                ['Certificación RETIE', format_currency(data['costSummary'].get('Certificación RETIE', 0))],
                ['Estudio de conexión', format_currency(data['costSummary'].get('Estudio de conexión', 0))],
                ['Medidor bidireccional', format_currency(data['costSummary'].get('Costo medidor bidireccional', 0))],
                ['Asesoría y Consultoría', format_currency(data['costSummary'].get('Asesoria y Consultoria especializada (2.5%)', 0))],
                ['Viáticos y transporte', format_currency(data['costSummary'].get('Viaticos y transporte', 0))],
                ['Imprevistos (4%)', format_currency(data['costSummary'].get('Imprevistos (4%)', 0))],
            ]
            
            if data['costSummary'].get('Protección CNO', 0) > 0:
                cost_items.insert(-2, ['Protección CNO', format_currency(data['costSummary']['Protección CNO'])])
            
            cost_table = Table(cost_items, colWidths=[4*inch, 2*inch])
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), ESMERALDA_VIVO),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Alinear costos a la derecha
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, PINO_OSCURO),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            elements.append(cost_table)
            elements.append(Spacer(1, 20))
            
            # Total
            elements.append(Paragraph(
                f"Total Estimado: {format_currency(data['totalCost'])}",
                ParagraphStyle(
                    'TotalStyle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    textColor=VERDE_CLOROFILA,
                    alignment=2  # Derecha
                )
            ))
            
            # Nota al pie
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(
                "* Los precios pueden variar según las condiciones del mercado y especificaciones finales del proyecto.",
                ParagraphStyle(
                    'Note',
                    parent=styles['Normal'],
                    fontSize=8,
                    textColor=colors.gray
                )
            ))
            
            # Construir el PDF
            doc.build(elements)
            return response
            
        except Exception as e:
            print(f"Error generando PDF: {str(e)}")
            return HttpResponse(f'Error generando PDF: {str(e)}', status=500)
    
    return HttpResponse('Método no permitido', status=405)
