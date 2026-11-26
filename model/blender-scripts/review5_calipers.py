"""Keep the exact photo endpoints behind the rounded, projected measurements."""
from math import dist
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

private = Path(__file__).resolve().parents[1] / "references/real/interior"
# ref (axis, endpoints, known mm), sample (name, endpoints). Pixel origin is top left.
plates = [
    ("pd-core.jpg", None, "Core PCB",
     [("x",(755,533),(265,533),100),("y",(748,533),(738,36),100)],
     [("Length","x",(303,325),(685,325)),("Width","y",(651,216),(651,399)),
      ("Outer IR centres","y",(561,270),(565,346))]),
    ("wd-008.jpg",None,"Motor control",
     [("x",(753,520),(287,516),40),("y",(827,193),(833,405),20)],
     [("Substrate width","x",(213,256),(592,256)),("Substrate height","y",(380,103),(380,438)),
      ("Contact projection","x",(592,251),(619,251))]),
    ("wd-010.jpg",None,"Navigation module",
     [("x",(619,460),(185,460),40),("y",(688,56),(692,241),20)],
     [("Substrate width","x",(161,167),(487,167)),("Board with tab","y",(343,40),(343,342)),
      ("Patch width","x",(246,147),(438,147))]),
    ("pd-overview.jpg",None,"Mouldings and cooling plate",
     [("x",(262,249),(335,249),38.7),("y",(296,193),(296,342),75)],
     [("Upper cover length","x",(278,118),(553,118)),("Upper cover width","y",(346,52),(346,183)),
      ("Belly panel length","x",(592,136),(730,136)),("Belly panel width","y",(654,97),(654,175)),
      ("Midframe length","y",(580,206),(580,465)),("Spreader length","x",(215,406),(356,406)),
      ("Spreader width","y",(276,372),(276,443))]),
    ("exterior-top.jpg",970,"Open arm reaches",
     [("p",(241,164),(749,531),213)],
     [("Front shoulder to motor","p",(371,448),(194,526)),("Rear shoulder to motor","p",(387,271),(241,164)),
      ("Front motor rim","p",(166,525),(226,525)),("Rear motor rim","p",(217,170),(266,170))]),
    ("exterior-front.jpg",640,"Camera in the nose",
     [("x",(56,327),(574,327),100)],
     [("Across outer caps","x",(249,251),(418,251)),("Face surround width","x",(287,249),(380,249))])]

lines=["# Projected photo measurements","",
       "Cyan lines are scale references. Gold lines are component spans. Pixel coordinates use the photo sizes below. An axis is calibrated independently where two rulers are visible. Rounded dimensions in the parts sheet allow for height above the ruler, perspective and endpoint choice.",""]
canvas=Image.new("RGB",(1320,930),"#ecede8")
draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf",19)
for i,(name,resize,head,refs,spans) in enumerate(plates):
    image=Image.open(private/name).convert("RGB")
    if resize:
        image=image.resize((resize,round(image.height*resize/image.width)),Image.Resampling.LANCZOS)
    g=ImageDraw.Draw(image)
    scales={}
    lines += [f"## {head}", "", f"[Photo]({name}) · measurement canvas {image.width} × {image.height} px.",""]
    for axis,a,b,known in refs:
        scales[axis]=dist(a,b)/known
        lines.append(f"- Scale {axis} · {a} to {b} = {known} mm.")
        g.line([a,b], fill="#20e3dc",width=3)
    lines.append("")
    for label,axis,a,b in spans:
        value=dist(a,b)/scales[axis]
        lines.append(f"- {label} · {a} to {b} · {value:.1f} mm projected.")
        g.line([a,b],fill="#ffc049",width=3)
        for x,y in (a,b):
            g.ellipse([x-3,y-3,x+3,y+3],fill="#ffc049")
    lines.append("")
    image.thumbnail((420,246),Image.Resampling.LANCZOS)
    x,y=(i%3)*440+10,(i//3)*455+15
    canvas.paste(image,(x,y))
    draw.text((x,y+259),head,font=font,fill="#142e33")
    for j,(label,axis,a,b) in enumerate(spans):
        draw.text((x,y+291+j*18),f"{label}   {dist(a,b)/scales[axis]:.0f} mm",fill="#294648",
                  font=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",14))
(private/"calipers.md").write_text("\n".join(lines)+"\n")
canvas.save(private/"calipers.jpg",quality=90)
