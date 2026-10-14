"""Local diagram rendering for the requirements report; no external service."""
from pathlib import Path
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont
from project_plan import calculate, START

ROOT=Path(__file__).resolve().parents[1]
NAVY='#19354D'; PALE='#E9EFF4'; INK='#17202A'; LINE='#718496'

def render(regular,bold):
    plan=ROOT/'docs/plans/images'; plan.mkdir(parents=True,exist_ok=True)
    usecases=ROOT/'docs/requirements/images'; usecases.mkdir(parents=True,exist_ok=True)
    def font(size,b=False): return ImageFont.truetype(bold if b else regular,size)
    def label(draw,xy,value,size=28,b=False,fill=INK,anchor=None):
        draw.text(xy,value,font=font(size,b),fill=fill,anchor=anchor)
    def arrow(draw,points,fill=LINE,width=4,dashed=False):
        if dashed:
            for first,last in zip(points,points[1:]):
                dx=last[0]-first[0]; dy=last[1]-first[1]; length=max(abs(dx),abs(dy))
                for offset in range(0,int(length),20):
                    stop=min(offset+11,length)
                    draw.line((first[0]+dx*offset/length,first[1]+dy*offset/length,
                               first[0]+dx*stop/length,first[1]+dy*stop/length),fill=fill,width=width)
        else: draw.line(points,fill=fill,width=width)
        end=points[-1]; before=points[-2]
        if end[0]>before[0]: head=[end,(end[0]-13,end[1]-8),(end[0]-13,end[1]+8)]
        elif end[0]<before[0]: head=[end,(end[0]+13,end[1]-8),(end[0]+13,end[1]+8)]
        elif end[1]>before[1]: head=[end,(end[0]-8,end[1]-13),(end[0]+8,end[1]-13)]
        else: head=[end,(end[0]-8,end[1]+13),(end[0]+8,end[1]+13)]
        draw.polygon(head,fill=fill)
    rows,duration,paths=calculate(); by_id={a['id']:a for a in rows}
    titles={'A':'Requirements','Q0':'CI / test baseline','B':'Review and PDF','C':'Analysis','D':'Architecture',
        'E':'Accounts','F':'Fridge','G':'Recipes','H':'Shopping / saved','I':'Responsive UI','Q1':'Shared TDD / CI',
        'J':'Integration','K':'Design report','L':'Design review','M':'Testing report','N':'Release / code'}
    positions={'A':(50,180),'Q0':(50,390),'B':(50,600),'C':(50,810),'D':(50,1020),
        'E':(550,180),'F':(550,390),'G':(550,600),'H':(550,810),'I':(550,1020),'Q1':(550,1230),
        'J':(1090,500),'K':(1090,940),'L':(1600,610),'M':(1600,850),'N':(1600,1090)}
    w,h=350,170
    im=Image.new('RGB',(2000,1580),'white'); d=ImageDraw.Draw(im)
    label(d,(50,25),'PERT network with parallel activities',44,True)
    label(d,(50,90),'Each node shows expected days, total slack, and earliest/latest start and finish offsets.',29)
    for a in rows:
        target=a['id']; tx,ty=positions[target]
        for parent in a['predecessors']:
            sx,sy=positions[parent]
            if parent=='A' and target=='B':
                points=[(sx,sy+h/2),(20,sy+h/2),(20,ty+h/2),(tx,ty+h/2)]
            elif parent=='Q0' and target=='Q1':
                points=[(sx+w,sy+h/2),(430,sy+h/2),(430,ty+h/2),(tx,ty+h/2)]
            elif sx==tx: points=[(sx+w/2,sy+h),(tx+w/2,ty)]
            else:
                lane=480 if parent=='D' else 980 if target in ('J','K') else 1510
                points=[(sx+w,sy+h/2),(lane,sy+h/2),(lane,ty+h/2),(tx,ty+h/2)]
            arrow(d,points)
    for a in rows:
        x,y=positions[a['id']]; critical=a['slack']==0
        d.rounded_rectangle((x,y,x+w,y+h),radius=12,fill=NAVY if critical else PALE,outline=NAVY,width=3)
        color='white' if critical else INK
        label(d,(x+w/2,y+30),f"{a['id']}  {titles[a['id']]}",29,True,color,'mm')
        label(d,(x+w/2,y+70),f"{a['duration']} days   |   slack {a['slack']}",27,False,color,'mm')
        label(d,(x+w/2,y+109),f"ES {a['es']}   EF {a['ef']}",27,False,color,'mm')
        label(d,(x+w/2,y+145),f"LS {a['ls']}   LF {a['lf']}",27,False,color,'mm')
    label(d,(50,1450),'Critical path: '+' > '.join(paths[0])+'   |   54 days',32,True)
    label(d,(50,1505),'Dark nodes have zero slack. Day 0 = 7 Oct. Finishes are exclusive. Planned finish 29 Nov.',28)
    im.save(plan/'pert.png')

    im=Image.new('RGB',(1900,1510),'white'); d=ImageDraw.Draw(im)
    label(d,(35,25),'Fridgely parallel work schedule',44,True)
    label(d,(35,85),'Expected calendar-day schedule from the same PERT forward pass. Estimates are proposed.',27)
    x0=620; x1=1840; scale=(x1-x0)/55
    for offset in range(0,55,7):
        x=x0+offset*scale
        label(d,(x,158),(START+timedelta(days=offset)).strftime('%d %b'),24,anchor='mm')
        d.line((x,190,x,1230),fill='#DBE2E8',width=2)
    for i,a in enumerate(rows):
        y=200+i*63
        label(d,(35,y+6),a['id']+'  '+titles[a['id']],29,True)
        sx=x0+a['es']*scale; ex=x0+a['ef']*scale; late=x0+a['lf']*scale
        if a['slack']:
            d.rectangle((ex,y+3,late,y+41),fill='#D9E5EE',outline=LINE,width=2)
        d.rounded_rectangle((sx,y,ex,y+44),radius=5,fill=NAVY if a['slack']==0 else '#577A97')
    label(d,(35,1260),'Dark bars: critical activities. Blue: noncritical. Pale extensions: total activity slack.',28)
    label(d,(35,1320),'Course deadlines: PR 8 Oct | PDF 11 Oct | Analysis 18 Oct | Design 15 Nov',29,True)
    label(d,(35,1375),'Testing 22 Nov | Code 30 Nov | Presentation TBA | Europe/Istanbul',29,True)
    label(d,(35,1430),'Expected internal finishes: design 14 Nov, testing 21 Nov, release 29 Nov. Reserve: 1 day.',27)
    im.save(plan/'gantt.png')

    im=Image.new('RGB',(1900,1530),'white'); d=ImageDraw.Draw(im)
    label(d,(45,25),'Fridgely use-case overview',44,True)
    boundary=(500,105,1430,1430)
    d.rectangle(boundary,outline=NAVY,width=4)
    label(d,(965,130),'Fridgely system',32,True,anchor='mm')
    uc=[('US-01','Register'),('US-02','Sign in'),('US-03','Save preferences'),('US-04','Add ingredient'),
        ('US-05','List ingredients and dates'),('US-06','Delete ingredient'),('US-07','Generate recipes'),
        ('US-08','View recipe details'),('US-09','Handle generation failure'),('US-10','Add missing ingredients'),
        ('US-11','Manage shopping list'),('US-12','Save favorite'),('US-13','Manage favorites'),('US-14','View recipe history')]
    centers={sid:205+i*80 for i,(sid,title) in enumerate(uc)}
    def actor(cx,cy,name):
        d.ellipse((cx-22,cy-60,cx+22,cy-16),outline=NAVY,width=4)
        d.line((cx,cy-16,cx,cy+53),fill=NAVY,width=4)
        d.line((cx-45,cy+12,cx+45,cy+12),fill=NAVY,width=4)
        d.line((cx,cy+53,cx-38,cy+100),fill=NAVY,width=4)
        d.line((cx,cy+53,cx+38,cy+100),fill=NAVY,width=4)
        label(d,(cx,cy+128),name,29,True,anchor='mm')
    actor(165,235,'Visitor'); actor(165,790,'Signed-in user'); actor(1705,430,'Recipe AI service')
    for index,(sid,title) in enumerate(uc):
        y=centers[sid]
        if index<2:
            d.line([(210,247),(350,247),(350,y),(550,y)],fill=LINE,width=3)
        elif sid!='US-09':
            d.line([(210,802),(420,802),(420,y),(550,y)],fill=LINE,width=3)
        d.ellipse((550,y-31,1380,y+31),fill=PALE,outline=NAVY,width=3)
        label(d,(965,y),sid+'  '+title,29,False,anchor='mm')
    gen=centers['US-07']; failure=centers['US-09']
    d.line([(1660,442),(1600,442),(1600,gen),(1380,gen)],fill=LINE,width=3)
    arrow(d,[(1380,failure),(1510,failure),(1510,gen),(1380,gen)],dashed=True)
    label(d,(1530,(failure+gen)/2),'<<extend>>',26)
    label(d,(550,1350),'US-15 constraint: authenticated, owner-only access to personal use cases.',26)
    label(d,(550,1390),'Failure extension: provider failure or invalid output. Details record history.',25)
    label(d,(45,1470),'Actors and use cases match the accompanying PlantUML source. Scope excludes OCR and expiry alerts.',27)
    im.save(usecases/'use-cases.png')
