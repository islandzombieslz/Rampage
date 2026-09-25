from pathlib import Path
import re

path = Path("index.html")
text = path.read_text(encoding="utf-8")

# Preserve the generated manifest: the cache generator will rebuild it from actual files.
manifest_pattern = re.compile(r'const BOOT_ASSET_MANIFEST=Object\.freeze\(\{.*?\}\);', re.S)
matches = list(manifest_pattern.finditer(text))
assert len(matches) == 1, "Expected exactly one generated asset manifest"
old_manifest = matches[0].group(0)
marker = "/* MENU_ASSET_MANIFEST_PLACEHOLDER */"
text = text[:matches[0].start()] + marker + text[matches[0].end():]

def replace_one(old, new):
    global text
    n = text.count(old)
    assert n == 1, f"Expected 1 occurrence; got {n}: {old[:90]!r}"
    text = text.replace(old, new, 1)

old_wallpaper = "assets/ui/walpaper-menus.png"
assert text.count(old_wallpaper) == 6, f"Unexpected wallpaper references: {text.count(old_wallpaper)}"
text = text.replace(old_wallpaper, "assets/ui/walpaper.gif")

replace_one(
    "#world{position:absolute;inset:0;width:100%;height:100%;display:block;background:#665642;touch-action:none}",
    "#world{position:absolute;inset:0;width:100%;height:100%;display:block;background:#080b10;touch-action:none}",
)

# Browser fullscreen requires a real user gesture. Any first click/tap now works on PC too.
replace_one(
    "if(!isMobileLike() || fullscreenRequestBusy)return isGameFullscreen();",
    "if(fullscreenRequestBusy)return isGameFullscreen();",
)
replace_one(
    "    // Reforça landscape toda vez que fullscreen é obtido/recuperado.\n"
    "    try{\n"
    "      if(window.screen.orientation?.lock){\n"
    "        await window.screen.orientation.lock('landscape');\n"
    "      }else if(window.screen.lockOrientation){\n"
    "        window.screen.lockOrientation('landscape');\n"
    "      }else if(window.screen.webkitLockOrientation){\n"
    "        window.screen.webkitLockOrientation('landscape');\n"
    "      }\n"
    "    }catch(_){}",
    "    // Orientation lock is appropriate only on touch/mobile devices.\n"
    "    if(isMobileLike()){\n"
    "      try{\n"
    "        if(window.screen.orientation?.lock){\n"
    "          await window.screen.orientation.lock('landscape');\n"
    "        }else if(window.screen.lockOrientation){\n"
    "          window.screen.lockOrientation('landscape');\n"
    "        }else if(window.screen.webkitLockOrientation){\n"
    "          window.screen.webkitLockOrientation('landscape');\n"
    "        }\n"
    "      }catch(_){}\n"
    "    }",
)
replace_one(
    "// Primeiro toque entra em fullscreen.\n"
    "function forceFullscreenFromGesture(){\n"
    "  if(!isMobileLike())return;\n"
    "  if(!isGameFullscreen())requestGameFullscreenLandscape().catch(()=>{});\n"
    "}",
    "// First click/tap also requests fullscreen on desktop; browsers forbid doing this on page load.\n"
    "function forceFullscreenFromGesture(){\n"
    "  if(!isGameFullscreen())requestGameFullscreenLandscape().catch(()=>{});\n"
    "}",
)
assert text.count("if(mobileStartHint){\n      mobileStartHint.style.display=isGameFullscreen()?'none':'flex';\n    }") == 1
text = text.replace(
    "if(mobileStartHint){\n      mobileStartHint.style.display=isGameFullscreen()?'none':'flex';\n    }",
    "if(mobileStartHint && isMobileLike()){\n      mobileStartHint.style.display=isGameFullscreen()?'none':'flex';\n    }",
    1,
)
replace_one(
    "function normalizeMobileViewport(){\n  if(!isMobileLike())return;",
    "function normalizeMobileViewport(){\n"
    "  // F11 and desktop browser fullscreen also change the canvas size/camera.\n"
    "  if(!isMobileLike()){resize();return;}",
)
replace_one(
    "  if(mobileStartHint)mobileStartHint.style.display=isGameFullscreen()?'none':'flex';",
    "  if(mobileStartHint && isMobileLike())mobileStartHint.style.display=isGameFullscreen()?'none':'flex';",
)
replace_one(
    "  if(state.mode==='war')clampWarCamera();\n}\naddEventListener('resize',normalizeMobileViewport);",
    "  if(state.mode==='war'){\n"
    "    if(!isMobileLike() && !state.camera.manual){\n"
    "      // Keep the complete arena in view after F11 or desktop window resize.\n"
    "      state.camera.intro=false;\n"
    "      state.camera.zoom=warCameraMinZoom();\n"
    "    }\n"
    "    clampWarCamera();\n"
    "  }\n"
    "}\naddEventListener('resize',normalizeMobileViewport);",
)

# Fit the entire 2200x1400 arena on desktop; center rather than crop either axis.
replace_one(
    "function warCameraMinZoom(){\n"
    " const {w,h}=gameViewport();\n"
    " if(isMobileLike())return .55;\n"
    " return Math.max(.55,w/state.world.w,h/state.world.h);\n"
    "}\n"
    "function clampWarCamera(){",
    "function warCameraMinZoom(){\n"
    " const {w,h}=gameViewport();\n"
    " if(isMobileLike())return .55;\n"
    " return Math.min(2.15,Math.max(.1,Math.min(w/state.world.w,h/state.world.h)));\n"
    "}\n"
    "function clampWarCameraAxis(position,worldSize,viewSize){\n"
    " if(viewSize>=worldSize)return (worldSize-viewSize)/2;\n"
    " return clamp(position,0,worldSize-viewSize);\n"
    "}\n"
    "function clampWarCamera(){",
)
replace_one(
    " state.camera.x=clamp(state.camera.x,0,Math.max(0,state.world.w-viewW));\n"
    " state.camera.y=clamp(state.camera.y,0,Math.max(0,state.world.h-viewH));",
    " state.camera.x=clampWarCameraAxis(state.camera.x,state.world.w,viewW);\n"
    " state.camera.y=clampWarCameraAxis(state.camera.y,state.world.h,viewH);",
)
replace_one(
    " c.zoom=Math.max(.72,warCameraMinZoom());",
    " c.zoom=isMobileLike()?Math.max(.72,warCameraMinZoom()):warCameraMinZoom();",
)
replace_one(
    " c.x=clamp(state.world.w/2-viewW/2,0,Math.max(0,state.world.w-viewW));\n"
    " c.y=clamp(state.world.h/2-viewH/2,0,Math.max(0,state.world.h-viewH));",
    " c.x=clampWarCameraAxis(state.world.w/2-viewW/2,state.world.w,viewW);\n"
    " c.y=clampWarCameraAxis(state.world.h/2-viewH/2,state.world.h,viewH);",
)
replace_one(
    " c.targetZoom=1.12;\n"
    " c.targetX=clamp(t.x-w/(2*c.targetZoom),0,Math.max(0,state.world.w-w/c.targetZoom));\n"
    " c.targetY=clamp(t.y-h/(2*c.targetZoom),0,Math.max(0,state.world.h-h/c.targetZoom));",
    " c.targetZoom=isMobileLike()?1.12:warCameraMinZoom();\n"
    " c.targetX=clampWarCameraAxis(t.x-w/(2*c.targetZoom),state.world.w,w/c.targetZoom);\n"
    " c.targetY=clampWarCameraAxis(t.y-h/(2*c.targetZoom),state.world.h,h/c.targetZoom);",
)
replace_one(
    "   zoom=state.camera.zoom;\n"
    "   clampWarCamera();\n"
    "   viewW=vw/zoom;viewH=vh/zoom;",
    "   clampWarCamera();\n"
    "   zoom=state.camera.zoom;\n"
    "   viewW=vw/zoom;viewH=vh/zoom;",
)
replace_one(
    "   left=clamp(left,0,Math.max(0,state.world.w-viewW));\n"
    "   top=clamp(top,0,Math.max(0,state.world.h-viewH));",
    "   left=clampWarCameraAxis(left,state.world.w,viewW);\n"
    "   top=clampWarCameraAxis(top,state.world.h,viewH);",
)
replace_one(
    " if(state.mode==='war'&&warFloorImage.complete&&warFloorImage.naturalWidth>0){\n"
    "   const dw=right-left,dh=bottom-top;\n"
    "   const sx=left/state.world.w*warFloorImage.naturalWidth;\n"
    "   const sy=top/state.world.h*warFloorImage.naturalHeight;\n"
    "   const sw=dw/state.world.w*warFloorImage.naturalWidth;\n"
    "   const sh=dh/state.world.h*warFloorImage.naturalHeight;\n"
    "   ctx.drawImage(warFloorImage,sx,sy,sw,sh,left,top,dw,dh);\n"
    " }else{\n"
    "   ctx.fillStyle='#665642';\n"
    "   ctx.fillRect(left,top,right-left,bottom-top);\n"
    " }",
    " // The arena may be smaller than the fullscreen viewport; letterbox the margins.\n"
    " const floorLeft=Math.max(0,left),floorTop=Math.max(0,top);\n"
    " const floorRight=Math.min(state.world.w,right),floorBottom=Math.min(state.world.h,bottom);\n"
    " const floorW=Math.max(0,floorRight-floorLeft),floorH=Math.max(0,floorBottom-floorTop);\n"
    " if(floorW>0&&floorH>0){\n"
    "   if(state.mode==='war'&&warFloorImage.complete&&warFloorImage.naturalWidth>0){\n"
    "     ctx.drawImage(warFloorImage,\n"
    "       floorLeft/state.world.w*warFloorImage.naturalWidth,\n"
    "       floorTop/state.world.h*warFloorImage.naturalHeight,\n"
    "       floorW/state.world.w*warFloorImage.naturalWidth,\n"
    "       floorH/state.world.h*warFloorImage.naturalHeight,\n"
    "       floorLeft,floorTop,floorW,floorH);\n"
    "   }else{\n"
    "     ctx.fillStyle='#665642';\n"
    "     ctx.fillRect(floorLeft,floorTop,floorW,floorH);\n"
    "   }\n"
    " }",
)

assert "https://i.postimg.cc/zvt1VzDv/walpaper.gif" not in text, "No external wallpaper URL may enter HTML"
assert text.count("assets/ui/walpaper.gif") == 6
assert marker in text
text = text.replace(marker, old_manifest, 1)
path.write_text(text, encoding="utf-8")
print("Wallpaper, fullscreen and arena camera patch applied (6 local wallpaper references).")
