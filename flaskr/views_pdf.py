from flask                        import Blueprint
from flask                        import request, make_response, abort, flash
from reportlab.pdfgen             import canvas
from reportlab.lib                import colors
from reportlab.lib.pagesizes      import A4, portrait
from reportlab.lib.units          import mm
from reportlab.pdfbase            import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts    import TTFont
from reportlab.platypus           import Table
from io                           import BytesIO
from flaskr                       import db,weeka
from flaskr.models                import Person,WorkRec
from datetime                     import datetime
from dateutil.relativedelta       import relativedelta

pdfmetrics.registerFont(TTFont('Gothic','flaskr/fonts/fonts-japanese-gothic.ttf'))
bp = Blueprint('pdf', __name__, url_prefix="/pdf")

def make_head(id,yymm):
    person = Person.query.filter_by(id=id).first()
    if person == None:
        return None

    head = {}
    yy = int(yymm[:4])
    gg = yy - 1988
    mm = int(yymm[4:])
    head['gm']     = '平成{gg}年{mm}月分'.format(gg=gg,mm=mm)
    head['name']   = person.name
    head['idm']    = person.idm
    head['number'] = person.number
    head['amount'] = person.amount
    return head

def make_items(id,yymm):
    yy     = int(yymm[:4])
    mm     = int(yymm[4:])
    first  = datetime(yy, mm, 1) 
    items  = []
    foot   = dict(
        sum = 0.0,
        cnt = 0
    )
    for dd in range(1,32):
        if mm != first.month:
            items.append(None)
            continue
        item = {}
        item['dd'] = first.day
        item['ww'] = weeka[first.weekday()]
        workrec = WorkRec.query.filter_by(person_id=id, yymm=yymm, dd=dd).first()
        if (workrec == None) or (workrec.value is None) or (workrec.value == 0.0):
            item['stat'] = '－'
        else:
            item['stat'] = '○'
            item['in']  = workrec.work_in
            item['out'] = workrec.work_out
            item['val'] = workrec.value
            foot['cnt'] = foot['cnt'] + 1
            foot['sum'] = foot['sum'] + workrec.value
        if first.weekday() != 6:
            items.append(item)
        first = first + relativedelta(days=1)
    while len(items) < 28:
        items.append(None)
    return items,foot

def make_pdf(head, items, foot):
    output = BytesIO()
    psize  = portrait(A4)
    xmargin = 15.0*mm
    p = canvas.Canvas(output, pagesize=psize, bottomup=True)
    # Title
    p.setFont('Gothic', 16)
    p.drawString(75*mm, 275*mm, '就労継続支援提供実績記録票')
    p.setFont('Gothic', 11)
    p.drawString(17*mm, 275*mm, head['gm'])
    # Header
    colw = (25.0*mm, 29.5*mm, 32.0*mm, 32.0*mm, 22.0*mm, 43.5*mm)
    idm = head['idm']
    data =[
        ['受給者証番号',head['number'],'支給決定障害者氏名',head['name'],'事業所番号','2317100929'],
        ['契約支給量',head['amount'],'','','事業者及び\nその事業所','オフィスファーム']
    ]
    table = Table(data, colWidths=colw, rowHeights=10.0*mm)
    table.setStyle([
        ('FONT',   ( 0, 0), (-1,-1), 'Gothic', 8),
        ('GRID',   ( 0, 0), (-1,-1), 0.5, colors.black),
        ('BOX',    ( 0, 0), (-1,-1), 1.8, colors.black),
        ('VALIGN', ( 0, 0), (-1,-1), 'MIDDLE'),
        ('ALIGN',  ( 0, 0), (-1,-1), 'CENTER'),
        ('ALIGN',  ( 1, 1), ( 1, 1), 'LEFT'),
        ('SPAN',   ( 1, 1), ( 3, 1))
    ])
    table.wrapOn(p, xmargin, 252.0*mm)
    table.drawOn(p, xmargin, 252.0*mm)
    # Detail
    colw = (8.6*mm,11.0*mm, 17.2*mm, 17.2*mm, 17.2*mm, 17.2*mm, 8.0*mm, 8.0*mm, 14.0*mm, 8.6*mm, 8.6*mm, 13.8*mm, 34.6*mm )
    data = [
        ['日\n付','曜\n日','サービス提供実績','','','','','','','','','利用者\n確認印','備考'],
        ['','','サービス提供\nの状況','開始時間','終了時間','利用時間','送迎加算','','`訪問支援特別加算','食事提供\n加算','施設外\n就労','',''],
        ['','','','','','','往','復','時間数'],
    ]
    for item in items:
        d = []
        if item != None:
            d.append(item['dd'])
            d.append(item['ww'])
            d.append(item['stat'])
            if 'in' in item:
                d.append(item['in'])
            else:
                d.append('')
            if 'out' in item:
                d.append(item['out'])
            else:
                d.append('')
            if 'val' in item:
                d.append(item['val'])
            else:
                d.append('')
        data.append(d)
    table = Table(data, colWidths=colw, rowHeights=7.0*mm)
    table.setStyle([
        ('FONT',   ( 0, 0), (-1,-1), 'Gothic', 9),
        ('FONT',   ( 2, 1), ( 2, 1), 'Gothic', 8),
        ('FONT',   ( 8, 1), ( 8, 1), 'Gothic', 5),
        ('FONT',   ( 9, 1), (10, 1), 'Gothic', 6),
        ('GRID',   ( 0, 0), (-1,-1), 0.5, colors.black),
        ('BOX',    ( 0, 0), (-1,-1), 1.8, colors.black),
        ('BOX',    ( 0, 0), (-1, 2), 1.8, colors.black),
        ('BOX',    ( 0, 0), ( 1,-1), 1.8, colors.black),
        ('BOX',    (11, 0), (11,-1), 1.8, colors.black),
        ('VALIGN', ( 0, 0), (-1,-1), 'MIDDLE'),
        ('ALIGN',  ( 0, 0), (-1, 2), 'CENTER'),
        ('ALIGN',  ( 0, 2), ( 5,-1), 'CENTER'),
        ('SPAN',   ( 0, 0), ( 0, 2)),
        ('SPAN',   ( 1, 0), ( 1, 2)),
        ('SPAN',   ( 2, 0), (10, 0)),
        ('SPAN',   ( 2, 1), ( 2, 2)),
        ('SPAN',   ( 3, 1), ( 3, 2)),
        ('SPAN',   ( 4, 1), ( 4, 2)),
        ('SPAN',   ( 5, 1), ( 5, 2)),
        ('SPAN',   ( 6, 1), ( 7, 1)),
        ('SPAN',   ( 9, 1), ( 9, 2)),
        ('SPAN',   (10, 1), (10, 2)),
        ('SPAN',   (11, 0), (11, 2)),
        ('SPAN',   (12, 0), (12, 2))
    ])
    table.wrapOn(p, xmargin, 32.0*mm)
    table.drawOn(p, xmargin, 32.0*mm)
    # Footer
    colw=(71.3*mm,17.1*mm,16.0*mm,14.0*mm,8.6*mm,13.6*mm,9.0*mm,34.5*mm)
    data=[
        ['合計','{}時間'.format(foot['sum']),'回','回','回','施設外\n就労','当月','日      '],
        ['','','','','','','累計','日      ']
    ]
    table = Table(data, colWidths=colw, rowHeights=4.0*mm)
    table.setStyle([
        ('FONT',   ( 0, 0), (-1,-1), 'Gothic', 8),
        ('FONT',   ( 1, 0), ( 4,-1), 'Gothic', 6),
        ('FONT',   ( 6, 0), ( 6,-1), 'Gothic', 6),
        ('GRID',   ( 0, 0), (-1,-1), 0.5, colors.black),
        ('BOX',    ( 0, 0), (-1,-1), 1.8, colors.black),
        ('VALIGN', ( 0, 0), (-1,-1), 'MIDDLE'),
        ('ALIGN',  ( 0, 0), ( 0,-1), 'CENTER'),
        ('ALIGN',  ( 1, 0), ( 4,-1), 'RIGHT'),
        ('ALIGN',  ( 5, 0), ( 6,-1), 'CENTER'),
        ('ALIGN',  ( 7, 0), ( 7,-1), 'RIGHT'),
        ('SPAN',   ( 0, 0), ( 0, 1)),
        ('SPAN',   ( 1, 0), ( 1, 1)),
        ('SPAN',   ( 2, 0), ( 2, 1)),
        ('SPAN',   ( 3, 0), ( 3, 1)),
        ('SPAN',   ( 4, 0), ( 4, 1)),
        ('SPAN',   ( 5, 0), ( 5, 1))
    ])
    table.wrapOn(p, xmargin, 23.2*mm)
    table.drawOn(p, xmargin, 23.2*mm)
    colw=(28.0*mm,21.5*mm,30.5*mm,21.5*mm,30.5*mm,21.5*mm,30.5*mm)
    data=[
        ['初期加算','利用開始日','','30日目','','当月算定日数','']
    ]
    table = Table(data, colWidths=colw, rowHeights=6.5*mm)
    table.setStyle([
        ('FONT',   ( 0, 0), (-1,-1), 'Gothic', 9),
        ('GRID',   ( 0, 0), (-1,-1), 0.5, colors.black),
        ('BOX',    ( 0, 0), (-1,-1), 1.8, colors.black),
        ('VALIGN', ( 0, 0), (-1,-1), 'MIDDLE'),
        ('ALIGN',  ( 0, 0), (-1,-1), 'CENTER')
    ])
    table.wrapOn(p, xmargin, 15.0*mm)
    table.drawOn(p, xmargin, 15.0*mm)
    # IDm
    p.setFont('Gothic', 11)
    p.drawString(17*mm, 10*mm, '記録ICカード：{idm}'.format(idm=idm))
    # Page Print
    p.showPage()
    p.save()
    result = output.getvalue()
    output.close()
    return result

@bp.route('/<id>/<yymm>')
def print_pdf(id,yymm):
    head = make_head(id, yymm)
    if head == None:
        abort(404)
    items,foot = make_items(id, yymm)
    if items == None:
        abort(404)
    response = make_response(make_pdf(head, items,foot))
    response.mimetype = 'application/pdf'
    return response
