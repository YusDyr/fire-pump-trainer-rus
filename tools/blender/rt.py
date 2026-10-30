import bpy, os, io, contextlib
DIR='/Users/dyr/YusDyr Vivo/NCPK_3D/blender'
g={'DIR':DIR,'__name__':'__main__'}
buf=io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    if REBUILD: exec(open(DIR+'/water_scene.py',encoding='utf-8').read(), g)
    sc=bpy.context.scene
    out=DIR+'/test'; os.makedirs(out,exist_ok=True)
    sc.render.image_settings.file_format='JPEG'; sc.render.resolution_percentage=50
    for f in FRAMES:
        sc.frame_set(f); sc.render.filepath=f'{out}/f{f:04d}.jpg'; bpy.ops.render.render(write_still=True)
result={'ok':True,'err':[l for l in buf.getvalue().splitlines() if 'Error' in l or 'Traceback' in l][:10]}
