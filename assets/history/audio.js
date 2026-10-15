/* Map-authored music only; combat SFX stay in the game's existing audio system. */
globalThis.RampageHistoryAudio = (() => {
  function bounds(config, audio) {
    const duration=Number.isFinite(audio.duration)?audio.duration:Number(config.duration)||0;
    let start=Math.max(0,Number(config.clipStart)||0),end=Number(config.clipEnd)||0;
    if(duration>0)start=Math.min(start,Math.max(0,duration-.01));
    if(!(end>start))end=duration>start?duration:Infinity;
    else if(duration>0)end=Math.min(end,duration);
    return {start,end};
  }
  function create(map) {
    const entries=new Map();let disposed=false;
    function seek(st,config) {try{st.audio.currentTime=bounds(config,st.audio).start}catch(_){}st.ended=false;}
    function play(st) {
      if(st.pending||!st.audio.paused)return;
      st.pending=true;
      try {
        Promise.resolve(st.audio.play()).then(()=>{
          st.fired=true;if(disposed||!st.want)st.audio.pause();
        }).catch(()=>{}).finally(()=>{st.pending=false;});
      }catch(_){st.pending=false;}
    }
    function suspend() {for(const st of entries.values()){st.want=false;st.audio.pause();}}
    function clear() {disposed=true;suspend();for(const st of entries.values()){st.audio.removeAttribute('src');st.audio.load();}entries.clear();}
    function update(player,enemies,objects,now=globalThis.performance?.now?.()??Date.now()) {
      if(disposed)return;
      const rows=(map.events||[]).filter(e=>e.kind==='sound'&&e.sound?.src).map(event=>({event,mix:globalThis.RampageHistoryRules.soundMix(event,map,objects,player,enemies)}));
      const winner=rows.filter(r=>r.event.sound.bus==='music'&&r.mix.active).sort((a,b)=>(Number(b.event.sound.priority)||0)-(Number(a.event.sound.priority)||0))[0];
      for(const row of rows) {
        const {event}=row;
        if(event.kind!=='sound'||!event.sound?.src)continue;
        const config=event.sound;
        let st=entries.get(event.id);
        if(!st) {
          const audio=new Audio(config.src);audio.preload='metadata';audio.loop=false;audio.volume=0;
          st={audio,fired:false,ended:false,pending:false,want:false,volume:0,lastAt:now};entries.set(event.id,st);
          audio.addEventListener('loadedmetadata',()=>seek(st,config),{once:true});
        }
        const mix={...row.mix,active:row.mix.active&&(config.bus!=='music'||row===winner)},clip=bounds(config,st.audio);
        const target=mix.active?mix.volume:0,dt=Math.min(.1,Math.max(0,(now-st.lastAt)/1000));st.lastAt=now;
        const fade=target>st.volume?(config.fadeIn??.22):(config.fadeOut??.55),step=fade>0?dt/fade:Infinity;
        st.volume=target>st.volume?Math.min(target,st.volume+step):Math.max(target,st.volume-step);st.audio.volume=st.volume;
        if(st.audio.currentTime<clip.start-.03)seek(st,config);
        if(st.audio.currentTime>=clip.end-.015 || st.audio.ended) {
          if(config.playMode==='loop'&&mix.active)seek(st,config);
          else {st.audio.pause();st.ended=true;try{st.audio.currentTime=clip.end}catch(_){} }
        }
        const mode=config.playMode||'loop';
        st.want=mix.active&&!st.ended;
        if(mode==='loop'&&mix.active)st.want=true;
        if(st.want&&(mode!=='once'||!st.fired))play(st);
        else if(!mix.active&&st.volume<=.002){st.audio.pause();st.volume=0;st.audio.volume=0;if(mode==='loop')seek(st,config);}
      }
    }
    return {entries,update,suspend,clear};
  }
  return {create,bounds};
})();
