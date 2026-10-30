import bpy, os, io, contextlib
DIR='/Users/dyr/YusDyr Vivo/NCPK_3D/blender'
g={'DIR':DIR,'__name__':'__main__'}
buf=io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    exec(open(DIR+'/water_scene.py',encoding='utf-8').read(), g)
    sc=bpy.context.scene; cam=bpy.data.objects['Камера']; tgt=bpy.data.objects['Цель камеры']
    out=DIR+'/test'; os.makedirs(out,exist_ok=True)
    sc.render.image_settings.file_format='JPEG'; sc.render.resolution_percentage=50
    names=[]
    for name,(f,key) in SHOTS.items():
        sc.frame_set(f)
        loc,t=g[key]
        cam.animation_data_clear(); tgt.animation_data_clear()
        cam.location=loc; tgt.location=t
        sc.render.filepath=f'{out}/shot_{name}.jpg'; bpy.ops.render.render(write_still=True); names.append(name)
result={'names':names,'err':[l for l in buf.getvalue().splitlines() if 'Error' in l or 'Traceback' in l][:10]}
