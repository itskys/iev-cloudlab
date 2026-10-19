# IEV CloudLab 官方视觉 Logo 全套资产包与前端部署使用说明 (V3 终版)

**适用站点**：`https://ievlab.aisai.cc/`  
**设计方案**：流线型智能电车气动剪影 + 立体双层 `iEV` 结构字标 + 数字孪生云算力节点  
**核心特性**：全部中英文字体已通过 `CoreText` 100% 转为纯数学矢量曲线 `<path>`（彻底消除跨平台字体缺失、间距错位、字母裁切与渐变回退黑字问题），并提供**白底高对比皇家蓝（Light Mode）**与**深空极光青（Dark Mode）**双主题全套配色。

---

## 一、 针对当前网站 (`https://ievlab.aisai.cc/`) 的两种实装部署方案

### 方案 A（最强烈推荐）：使用「纯图形标 (`logo-mark`)」配合网页原有 HTML 文字
> **适用原因**：当前网站的顶部导航栏（Header）和中间登录卡片（Login Box）在 HTML DOM 中**本身已写有 `IEV CloudLab` 和 `智能电动汽车云仿真实验平台` 文字**。直接将 `<img>` 替换为不含右侧重复文字的纯图形标，不仅彻底消除文字重复，还能让流线型电车图标放大近一倍，视觉冲击力最强。

```html
<!-- 1. 顶部导航栏左上角 (配合右侧 HTML 文字) -->
<!-- 白底浅色模式默认引用 logo-mark-light.svg；切换到深色模式时引用 logo-mark-dark.svg -->
<img src="/assets/logo-mark-light.svg" alt="IEV CloudLab" style="height: 40px; width: auto; object-fit: contain;" />

<!-- 2. 登录框卡片顶部居中 (配合下方 HTML 标题) -->
<img src="/assets/logo-mark-light.svg" alt="IEV CloudLab" style="height: 64px; width: auto; margin-bottom: 8px;" />
```

---

### 方案 B：隐藏网页 HTML 文字，单用一张「完整横向图文组合标 (`logo-navbar`)」
> **适用场景**：如果前端希望把网页里的文字标签删掉，只用一个 `<img>` 同时展示「电车图标 + 分割线 + IEV CloudLab + 中英文双副标题」。

```html
<!-- 白底浅色导航栏 / 登录框 -->
<img src="/assets/logo-navbar-light.svg" alt="IEV CloudLab" style="height: 46px; width: auto;" />

<!-- 深色导航栏 / 深色背景 -->
<img src="/assets/logo-navbar.svg" alt="IEV CloudLab" style="height: 46px; width: auto;" />

<!-- 若希望左侧图形已有 iEV、右侧只显示 CloudLab（不重复出现 IEV）：使用紧凑版 -->
<img src="/assets/logo-navbar-compact-light.svg" alt="IEV CloudLab" style="height: 44px; width: auto;" />
```

---

### 深浅主题自动切换代码示例（支持网页右上角 `◐` 按钮）
如果网页使用 `<picture>` 或 CSS 类名切换深浅色主题，可直接采用以下代码：

```html
<header class="site-header">
  <img src="/assets/logo-mark-light.svg" class="logo-light" alt="IEV CloudLab" style="height: 40px;" />
  <img src="/assets/logo-mark-dark.svg"  class="logo-dark"  alt="IEV CloudLab" style="height: 40px;" />
</header>

<style>
  /* 默认浅色模式显示 light 图标 */
  .logo-dark { display: none; }
  /* 当 html 或 body 带有 dark 类名时自动切换深色流光图标 */
  html.dark .logo-light, body.dark .logo-light { display: none; }
  html.dark .logo-dark,  body.dark .logo-dark  { display: inline-block; }
</style>
```

---

## 二、 压缩包目录结构与全套 50 个文件清单

双击根目录下的 **`PREVIEW_视觉预览中心.html`**（或 `assets/index.html`），即可在浏览器中直观查看 1:1 模拟网页登录页与所有背景对比效果。

### 1. `01_SVG_Vector/`（12 款全转曲原生矢量源文件，无损缩放，前端首选）
| 文件名 | 适用背景 | 布局结构说明 |
|---|---|---|
| `logo-mark-lighttheme-transparent.svg` | **浅色/白底**（透明通道） | **纯图形标**（深海皇家蓝 `#003EB3` → 翡翠青 `#00A896`，最适合当前白底网页） |
| `logo-mark-darktheme-transparent.svg` | **深色背景**（透明通道） | **纯图形标**（电光青 `#00D4FF` → 薄荷绿 `#00E8A2`） |
| `logo-navbar-full-lighttheme-transparent.svg` | **浅色/白底**（透明通道） | 完整横标：`[iEV 图形] | IEV CloudLab` + 中英文双副标题（全矢量转曲路径） |
| `logo-navbar-full-darktheme-transparent.svg` | **深色背景**（透明通道） | 完整横标：`[iEV 图形] | IEV CloudLab` + 中英文双副标题（纯白+极光青渐变） |
| `logo-navbar-compact-lighttheme-transparent.svg` | **浅色/白底**（透明通道） | 紧凑横标：`[iEV 图形] | CloudLab`（不重复 IEV，适合窄导航栏） |
| `logo-navbar-compact-darktheme-transparent.svg` | **深色背景**（透明通道） | 紧凑横标：`[iEV 图形] | CloudLab`（深色主题版） |
| `logo-vertical-lighttheme-transparent.svg` | **浅色/白底**（透明通道） | 立式居中组合标（1:1 正方形构图，上图标下文字） |
| `logo-vertical-darktheme-transparent.svg` | **深色背景**（透明通道） | 立式居中组合标（深色主题带柔和径向光晕） |
| `logo-navbar-bg-obsidian-dark.svg` / `slate-navy.svg` / `daylight-white.svg` | 自带实色背景 | 分别自带深空黑（`#070B14`）、科技蓝灰（`#1E293B`）、纯净白昼（`#FFFFFF`）背景的横标 |
| `favicon.svg` / `og-banner-1200x630.svg` | 浏览器标签 / 社交卡片 | 矢量 Favicon 与 1200×630 社交分享海报源文件 |

---

### 2. `02_PNG_Transparent_For_Dark_BG/`（9 款深色背景专用 32位全透明 PNG）
- **纯图形透明底**：`logo-mark-transparent-1200x512.png`、`logo-mark-transparent-600x256.png`
- **完整横标透明底**：`logo-navbar-full-transparent-1600x400.png`、`800x200.png`、`400x100.png`
- **紧凑横标透明底**：`logo-navbar-compact-transparent-1600x400.png`、`800x200.png`
- **立式居中透明底**：`logo-vertical-transparent-1024x1024.png`、`512x512.png`

---

### 3. `03_PNG_Transparent_For_Light_BG/`（9 款浅色/白底专用 32位全透明 PNG）
> 专门针对当前白底网页、Word 文档、PPT 汇报、学术论文调校的高对比度透明 PNG：
- **纯图形透明底**：`logo-mark-lightmode-transparent-1200x512.png`、`logo-mark-lightmode-transparent-600x256.png`
- **完整横标透明底**：`logo-navbar-full-lightmode-transparent-1600x400.png`、`800x200.png`、`400x100.png`
- **紧凑横标透明底**：`logo-navbar-compact-lightmode-transparent-1600x400.png`、`800x200.png`
- **立式居中透明底**：`logo-vertical-lightmode-transparent-1024x1024.png`、`512x512.png`

---

### 4. `04_PNG_With_Backgrounds/`（7 款自带多背景成品图）
无需额外设置背景色，开箱即用，包含三种精心调校的底色：
1. **深空黑曜石 (`obsidian-dark`, `#070B14`)**：`1024×1024`、`512×512`（立式）与 `1600×400`（横式）
2. **科技深蓝灰 (`slate-navy`, `#1E293B`)**：`1024×1024`（立式）与 `1600×400`（横式）
3. **纯净白昼 (`daylight-white`, `#FFFFFF`)**：`1024×1024`（立式）与 `1600×400`（横式）

---

### 5. `05_Favicons_and_App_Icons/`（10 款全平台浏览器图标与配置文件）
- `favicon.ico`：内嵌 `16×16`、`32×32`、`48×48` 三重分辨率复合图标
- `favicon-16x16.png`、`32x32.png`、`48x48.png`、`64x64.png`、`128x128.png`
- `apple-touch-icon-180x180.png`（iOS 添加到主屏幕专用）
- `android-chrome-192x192.png`、`512x512.png` + `site.webmanifest`（PWA 标准配置）

---

### 6. `06_Social_and_Hero_Banners/`（2 款社交分享卡片与首屏宽屏大图）
- `og-social-card-1200x630.png`：用于微信、Slack、Discord、Twitter 分享网址时的预览大图
- `hero-banner-1920x1080.png`：1080P 全高清宽屏展示海报

---

## 三、 品牌标准色值表（Design Tokens）

| 色彩角色 | 浅色模式 (Light Mode) | 深色模式 (Dark Mode) | 用途说明 |
|---|---|---|---|
| **主品牌蓝 (Primary Blue)** | `#155EEF` / `#003EB3` | `#0077FF` | 登录主按钮、车尾与字标基底 |
| **科技电光青 (Cyber Cyan)** | `#0066FF` | `#00E5FF` | 车身流线、云节点、发光分割线 |
| **电能翡翠绿 (Energy Mint)** | `#00A896` | `#00E8A2` | 车头高光、算力脉冲端点 |
| **主标题色 (Heading Text)** | `#0F172A` (深曜石黑蓝) | `#FFFFFF` (纯白) | `IEV` 主字标与页面主标题 |
| **副标题色 (Subtitle Text)** | `#475569` / `#64748B` | `#94A3B8` | 中英文副标题与说明文字 |
