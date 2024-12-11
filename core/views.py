from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import xmlrpc.client
from .models import DatosExternos, TipoTeja, Viaticos, Ubicacion, Estudio_conexion
from django.http import JsonResponse
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
import os

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
        panel_area = (panel['module_length'] * panel['module_width']) / 10 
        panel_sales_count = panel['sales_count']
        panel_price = panel['list_price']
        paneles_data.append({'id': panel_id, 'name': panel_name, 'power': panel_power, 'panel_area': panel_area, 'sales_count': panel_sales_count, 'panel_price': panel_price})
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

# Registrar fuentes personalizadas
pdfmetrics.registerFont(TTFont('MADE_AWELIER', 'static/fonts/MADE_AWELIER.ttf'))
pdfmetrics.registerFont(TTFont('NUNITO_SANS', 'static/fonts/NunitoSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NUNITO_SANS_BOLD', 'static/fonts/NunitoSans-Bold.ttf'))

#Reporte pdf
# Definimos los colores de la paleta
VERDE_CLOROFILA = Color(0.039, 0.239, 0.200)  # #0a3d33
PINO_OSCURO = Color(0.102, 0.318, 0.267)      # #1a512e
ESMERALDA_VIVO = Color(0.227, 0.655, 0.208)   # #3aa735
CYAN_PROFUNDO = Color(0.000, 0.529, 0.463)    # #008776

VERDE_HERSIC = Color(0.33, 0.67, 0.24)
VERDE_OSCURO = Color(0.20, 0.47, 0.17)
AZUL_TABLA = Color(0.06, 0.32, 0.55)

class PDFWithHeaderFooter(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        self.client_data = kwargs.pop('client_data', {})
        super().__init__(*args, **kwargs)
        self.page_width = letter[0]
        self.page_height = letter[1]

    def header(self, canvas, doc):
        canvas.saveState()
        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), 'static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, doc.leftMargin + 400, 
                           self.page_height - 70, width=100, height=40)

        # Título con MADE AWELIER
        canvas.setFillColor(colors.green)
        canvas.rect(doc.leftMargin - 10, self.page_height - 60, 
                   200, 30, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont('MADE_AWELIER', 16)
        canvas.drawString(doc.leftMargin, self.page_height - 50, 
                         "PROPUESTA ECONÓMICA")
        
        # Barra decorativa inferior
        footer_path = os.path.join('static', 'img', 'footer.png')
        if os.path.exists(footer_path):
            canvas.drawImage(footer_path, 0, doc.bottomMargin - 45, 
                           width=self.page_width, height=25)
        canvas.restoreState()
        

def format_currency(amount):
    """Formatea números a formato de moneda sin decimales"""
    try:
        if isinstance(amount, str):
            amount = amount.replace('$', '').replace(',', '').strip()
        return "${:,.0f}".format(float(amount))
    except (ValueError, TypeError):
        return "$0"

def generate_quote_table(data):
    """Genera la tabla de cotización detallada"""
    headers = [
        ['Componente', 'Cantidad', 'Precio unitario sin IVA e instalacion', 'Total']
    ]
    
    items = []
    cost_summary = data['costSummary']
    
    # Orden específico de los items
    item_order = [
        "Costo panel(es)",
        "Costo inversor (es)",
        "Costo ExportManager",
        "Costo de CTSolis",
        "Costo de protector(es) inversor(es)",
        "Teja",
        "Material eléctrico",
        "Certificación RETIE",
        "Estudio de conexión",
        "Costo medidor bidireccional",
        "Protección CNO",
        "Asesoria y Consultoria especializada (2.5%)",
        "Viaticos y transporte",
        "Imprevistos (4%)",
    ]

    # Agregar items en el orden especificado
    for key in item_order:
        value = cost_summary.get(key)
        if value and isinstance(value, dict) and value.get('total'):
            items.append([
                value.get('nombreProducto', key),
                str(value.get('cantidad', '')),
                format_currency(value.get('precioUnitario', 0)),
                format_currency(value.get('total', 0))
            ])
    # Agregar subtotal y total
    total_sin_iva = cost_summary.get('Costo sin IVA').get('total')
    total = cost_summary.get('Costo Total').get('total')
    
    # Agregar filas de totales
    items.append([''] * 4)  # Fila vacía para espaciado
    items.append(['Subtotal (Productos sin IVA)', '', '', format_currency(total_sin_iva)])
    items.append(['Total a pagar', '', '', format_currency(total) ])
    #AQUI SE PODRIA PONER TOTAL DESPUES DE DESCUENTO Y HALAR LOS DATOS DESDE UNA BD (FUTUTO)
    
    table = Table(headers + items, colWidths=[2.15*inch, 0.75*inch, 2.8*inch, 1.2*inch])
    table.setStyle(TableStyle([
        # Estilos para el encabezado
        ('BACKGROUND', (0, 0), (-1, 0), VERDE_HERSIC),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Estilos para las filas de datos
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinear nombres a la izquierda
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Alinear números a la derecha
        
        # Grilla y espaciado
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # Línea más gruesa después del encabezado
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
    ]))
    
    
    # Aplicar estilos específicos para las últimas filas
    for i in range(-2, 0):
        table.setStyle(TableStyle([
            ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
            ('FONTSIZE', (0, i), (-1, i), 10),
            ('BACKGROUND', (0, i), (-1, i), colors.lightgrey),
            ('ALIGN', (0, i), (0, i), 'RIGHT'),  # Alinear "Subtotal", "IVA" y "Total" a la derecha
        ]))
    
    return table

def generate_amortization_table(total_amount, years):
    """Genera la tabla de amortización con menos columnas y sin decimales"""
    headers = [
        ['Nº', 'CUOTA', 'PRINCIPAL', 'INTERÉS', 'SALDO FINAL']
    ]
    
    monthly_rate = 0.018
    months = years * 12
    monthly_payment = total_amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    
    balance = total_amount
    rows = []
    
    for i in range(1, months + 1):
        interest = balance * monthly_rate
        principal = monthly_payment - interest
        balance = max(0, balance - principal)
        
        row = [
            str(i),
            format_currency(monthly_payment),
            format_currency(principal),
            format_currency(interest),
            format_currency(balance)
        ]
        rows.append(row)
    
    table = Table(headers + rows, 
                 colWidths=[0.7*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_TABLA),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'NUNITO_SANS_BOLD'),
        ('FONTNAME', (0, 1), (-1, -1), 'NUNITO_SANS'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    return table

def generate_pdf(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_type = data.get('paymentType', 'contado')
            credit_years = int(data.get('creditYears', 0))
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Cotizacion-{data["fullName"]}.pdf"'
            
            doc = PDFWithHeaderFooter(
                response,
                pagesize=letter,
                rightMargin=65,
                leftMargin=65,
                topMargin=120,
                bottomMargin=72,
                client_data=data
            )
            
            elements = []
            
            # Información del cliente
            client_info = [
                ['Asunto:', 'Propuesta Económica Sistema Fotovoltaico conectado a red'],
                ['Tipo de cliente:', 'Residencial'],
                ['Asesor:', 'Hersic International'],
                ['Nombre del cliente:', data['fullName']],
                ['Fecha de cotización:', data['date']],
            ]
            
            table = Table(client_info, colWidths=[1.5*inch, 5*inch])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 30))  # Más espacio entre elementos
            
            # Texto introductorio
            elements.append(Paragraph("""
                Para HERSIC INTERNATIONAL es un gusto presentar la propuesta de energía solar con respecto a los requerimientos de su vivienda.
                """, ParagraphStyle('Normal')))
            elements.append(Spacer(1, 7))

            elements.append(Paragraph("""
                HERSIC INTERNATIONAL es una empresa dedicada a ofrecer soluciones integrales en energía fotovoltaica, alumbrado público y energía termo solar; como fabricantes de nuestros productos podemos ofrecer competitividad y nuestra más alta experiencia para todo lo que ustedes necesitan en el campo de la energía solar.
                """, ParagraphStyle('Normal')))
            elements.append(Spacer(1, 7))

            elements.append(Paragraph("""
                Contamos con soporte de alta ingeniería en todo nuestro con un equipo técnico deseoso de orientar y/o solucionar cualquier problema en su empresa.
                Entre algunas áreas que nos enfocamos está el soporte técnico especializado a nuestros distribuidores, financiación para contratos PPAs, ejecución de proyectos con el cumplimiento de las normas técnicas nacionales e internacionales en el segmento comercial e industrial, como el acompañamiento y asesoría en temas como beneficios tributarios para sistemas solares fotovoltaicos entre otros. 
                """, ParagraphStyle('Normal')))
            elements.append(Spacer(1, 7))

            elements.append(Paragraph("""
                Tengan ustedes la plena garantía que cuentan con el mayor respaldo y soporte, además de un robusto y completo portafolio con excelentes garantías.
                """, ParagraphStyle('Normal')))
            elements.append(Spacer(1, 7))
            

            elements.append(Paragraph("""
                Tengan ustedes la plena garantía que cuentan con el mayor respaldo y soporte, además de un robusto y completo portafolio con excelentes garantías.
                De antemano muchas gracias por contar con HERSIC y permitirnos presentarles nuestra propuesta. Quedamos a su entera disposición para cualquier inquietud que tengan sobre ésta
                """, ParagraphStyle('Normal')))
            elements.append(Spacer(1, 30))

            # Tabla de datos del usuario
            system_info = [
                ['Datos del cliente', 'Valor'],
                ['Consumo mensual', f"{data['consumption']} kWh"],
                ['Costo por kWh', format_currency(data['costPerKwh'])],
                ['Área disponible', f"{data['availableArea']} m²"],
                ['Transformador', f"{data['transformer']} kVA"],
            ]
            
            # Crear tabla de información del sistema
            system_table = Table(system_info, colWidths=[4*inch, 2.9*inch])
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
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(system_table)
            elements.append(Spacer(1, 20))
            elements.append(PageBreak())
            
            # Tabla de cotización
            elements.append(generate_quote_table(data))
            elements.append(Spacer(1, 20))
            
            # Si es pago a crédito, agregar tabla de amortización
            if payment_type == 'credito' and credit_years > 0:
                elements.append(PageBreak())
                elements.append(Paragraph('Plan de Amortización', 
                                       ParagraphStyle('Heading1',
                                                      fontSize=20,
                                                      alignment=TA_CENTER)))
                elements.append(Spacer(1, 50))
                
                # Crear la tabla de amortización en landscape
                total_amount = float(data['totalCost'].replace('$', '').replace(',', ''))
                elements.append(generate_amortization_table(total_amount, credit_years))
            doc.build(elements, onFirstPage=doc.header, onLaterPages=doc.header)
            return response
            
        except Exception as e:
            print(f"Error generando PDF: {str(e)}")
            return HttpResponse(f'Error generando PDF: {str(e)}', status=500)
    
    return HttpResponse('Método no permitido', status=405)