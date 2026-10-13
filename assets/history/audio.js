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
    function update(player,enemies,objects) {
      if(disposed)return;
      for(const event of map.events||[]) {
        if(event.kind!=='sound'||!event.sound?.src)continue;
        const config=event.sound;
        let st=entries.get(event.id);
        if(!st) {
          const audio=new Audio(config.src);audio.preload='metadata';audio.loop=false;
          st={audio,fired:false,ended:false,pending:false,want:false};entries.set(event.id,st);
          audio.addEventListener('loadedmetadata',()=>seek(st,config),{once:true});
        }
        const mix=globalThis.RampageHistoryRules.soundMix(event,map,objects,player,enemies),clip=bounds(config,st.audio);
        st.audio.volume=mix.volume;
        if(st.audio.currentTime<clip.start-.03)seek(st,config);
        if(st.audio.currentTime>=clip.end-.015 || st.audio.ended) {
          if(config.playMode==='loop'&&mix.active)seek(st,config);
          else {st.audio.pause();st.ended=true;try{st.audio.currentTime=clip.end}catch(_){} }
        }
        const mode=config.playMode||'loop';
        st.want=mode==='once' ? !st.ended&&(mix.active||st.fired) : mix.active&&(mode==='loop'||!st.ended);
        if(st.want)play(st);
        else {st.audio.pause();if(mode==='loop')seek(st,config);}
      }
    }
    return {entries,update,suspend,clear};
  }
  return {create,bounds};
})();
