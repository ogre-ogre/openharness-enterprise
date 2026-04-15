import paramiko
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

# Python生成PPT的代码片段，添加到SKILL.md开头
python_pptx_section = '''
## Python直接生成PPT（推荐）

**由于服务器Node.js兼容性问题，请使用 python-pptx 库直接生成PPT文件。**

### 基本用法

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

# 获取保存路径
downloads_path = os.environ.get("OH_DOWNLOADS_PATH", "/tmp")
output_file = os.path.join(downloads_path, "presentation.pptx")

# 创建演示文稿
prs = Presentation()
prs.slide_width = Inches(10)  # 16:9比例
prs.slide_height = Inches(5.625)

# 添加标题幻灯片
slide_layout = prs.slide_layouts[0]  # 标题幻灯片布局
slide = prs.slides.add_slide(slide_layout)

# 设置标题
title = slide.shapes.title
title.text = "演示标题"
title.text_frame.paragraphs[0].font.size = Pt(44)
title.text_frame.paragraphs[0].font.bold = True
title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 51, 102)

# 设置副标题
subtitle = slide.placeholders[1]
subtitle.text = "副标题"

# 添加内容幻灯片
slide_layout = prs.slide_layouts[1]  # 标题和内容布局
slide = prs.slides.add_slide(slide_layout)
title = slide.shapes.title
title.text = "第一页标题"

# 添加文本框
left = Inches(1)
top = Inches(2)
width = Inches(8)
height = Inches(3)
textbox = slide.shapes.add_textbox(left, top, width, height)
tf = textbox.text_frame
tf.text = "这里是内容文本"

# 添加列表
p = tf.paragraphs[0]
p.text = "要点一"
p.level = 0
p = tf.add_paragraph()
p.text = "要点二"
p.level = 0
p = tf.add_paragraph()
p.text = "子要点"
p.level = 1

# 保存文件
prs.save(output_file)
print(f"PPT已保存到: {output_file}")
```

### 常用功能

#### 设置背景颜色
```python
from pptx.enum.shapes import MSO_SHAPE

# 添加矩形作为背景
shape = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE,
    Inches(0), Inches(0),
    prs.slide_width, prs.slide_height
)
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(26, 26, 26)  # 深色背景
shape.line.fill.background()  # 无边框
```

#### 添加图片
```python
# 添加图片
slide.shapes.add_picture(
    "image.png",
    Inches(1), Inches(1),
    width=Inches(4)
)
```

#### 自定义字体样式
```python
from pptx.enum.text import PP_ALIGN

para = tf.paragraphs[0]
para.font.name = "Arial"
para.font.size = Pt(24)
para.font.bold = True
para.font.italic = False
para.font.color.rgb = RGBColor(255, 255, 255)  # 白色
para.alignment = PP_ALIGN.CENTER
```

---

'''

# 读取现有SKILL.md
skill_md_path = '/home/ai-app/.oh-enterprise/shared/skills/pptx/SKILL.md'
try:
    with sftp.open(skill_md_path) as f:
        original_content = f.read().decode('utf-8')
    
    # 在"## Creating a new PowerPoint presentation"之前插入Python方案
    insert_marker = '## Creating a new PowerPoint presentation **without a template**'
    
    if insert_marker in original_content and '## Python直接生成PPT' not in original_content:
        # 找到插入位置
        insert_pos = original_content.find(insert_marker)
        new_content = original_content[:insert_pos] + python_pptx_section + original_content[insert_pos:]
        
        # 写回文件
        with sftp.open(skill_md_path, 'w') as f:
            f.write(new_content.encode('utf-8'))
        
        print('[OK] SKILL.md updated with Python-pptx section')
    else:
        print('[INFO] SKILL.md already has Python section or marker not found')
        
except Exception as e:
    print(f'[ERROR] {e}')

sftp.close()
ssh.close()