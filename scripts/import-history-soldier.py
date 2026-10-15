"""Keep supplied soldier GIFs and build bounded display copies with every frame."""
import pathlib,json,sys,shutil
from PIL import Image,GifImagePlugin
root=pathlib.Path(__file__).resolve().parents[1];src=pathlib.Path(sys.argv[1]);dest=root/'assets/history/soldier-enemy';dest.mkdir(parents=True,exist_ok=True)
names={'idle':'enemy soldier parado.gif','walk':'enemy soldier andando.gif','death':'enemy soldier morrendo.gif','combo1':'soldier ataque combo.gif','combo2':'soldier ataque combo 2.gif'};config={'hp':100,'shield':50,'damage':10,'range':112,'speed':117,'hitFractions':[0,.25,.5,.75,.985],'sprites':{}}
for key,name in names.items():
 original=dest/(key+'-original.gif');shutil.copyfile(src/name,original)
 frames=[];durations=[]
 with Image.open(original) as image:
  loop=image.info.get('loop',0)
  for i in range(image.n_frames):
   image.seek(i);durations.append(image.info.get('duration',0));rgba=image.convert('RGBA').resize((256,256),Image.Resampling.LANCZOS);alpha=rgba.getchannel('A');p=rgba.convert('RGB').quantize(colors=255,method=Image.Quantize.FASTOCTREE);frame=p.point([min(255,x+1) for x in range(256)]);palette=p.getpalette()[:765];frame.putpalette([0,0,0]+palette+[0]*(765-len(palette)));frame.paste(0,mask=alpha.point([255 if x<128 else 0 for x in range(256)]));frames.append(frame)
 target=dest/(key+'.gif')
 with target.open('wb') as f:
  header,_=GifImagePlugin.getheader(frames[0],info={'loop':loop,'background':0})
  for block in header:f.write(block)
  for frame,duration in zip(frames,durations):
   for block in GifImagePlugin.getdata(frame,duration=duration,transparency=0,disposal=2,include_color_table=True):f.write(block)
  f.write(b';')
 config['sprites'][key]={'src':target.relative_to(root).as_posix(),'source':original.relative_to(root).as_posix(),'frames':len(frames),'durationMs':sum(durations)}
(root/'assets/history/soldier-config.json').write_text(json.dumps(config,separators=(',',':'))+'\n');print(config)
