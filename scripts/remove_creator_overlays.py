from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
marker = 'RISELOOTER_CREATOR_OVERLAY_CLEANUP_V22'
if marker in s:
    print('cleanup already applied')
    raise SystemExit(0)

css = r'''
/* RISELOOTER_CREATOR_OVERLAY_CLEANUP_V22 */
/* Never draw synthetic skin/hair shapes over the character preview. */
#creatorModal .creator-skin-overlay,
#creatorModal .creator-hair-overlay,
#creatorModal .creator-preview-stage .creator-skin-overlay,
#creatorModal .creator-preview-stage .creator-hair-overlay{
  display:none!important;
  visibility:hidden!important;
  opacity:0!important;
  background:none!important;
  clip-path:none!important;
}
/* Keep the validated source artwork crisp and untouched. */
#creatorModal .creator-preview-person,
#creatorModal .creator-preview > img{
  filter:none!important;
  mix-blend-mode:normal!important;
}
'''

s = s.replace('</style>', css + '\n</style>', 1)
p.write_text(s, encoding='utf-8')
print('creator overlays disabled')
