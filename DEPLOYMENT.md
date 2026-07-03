# 佈署流程 (Deployment Guide) — 搬到另一台 4060 筆電

## 為什麼不整套 Docker 化？

Docker Desktop on Windows 底層是跑在 WSL2 的 Linux VM 裡，**USB/內建鏡頭沒辦法
像 Linux 主機那樣直接掛進容器**，要用的話得靠 [usbipd-win](https://github.com/dorssel/usbipd-win)
把鏡頭通到 WSL2，步驟繁瑣、部分鏡頭驅動還不穩。

但這其實不影響「用內建鏡頭」這件事——**只有 YOLO 這個會碰鏡頭的程式需要跑在容器
外面**，資料庫完全不需要碰硬體，本來就該 Docker 化。所以正確拆法是:

```
Docker           →  postgres（PostGIS，不碰硬體，永遠 Docker 化最單純）
原生 Windows 程序 →  backend（YOLO 讀鏡頭 + GPU 推論）、frontend（網頁）
```

backend 原生跑在 Windows 上，讀內建鏡頭就跟一般裝了 OpenCV 的 Python 程式一樣，
完全不用碰 WSL2/usbipd。下面的 [start.ps1](start.ps1) 腳本把「複製資料夾 →
建置 → 啟動全部服務」包成一步，複製過去跑一次就好，不需要手動改任何設定。

## 一鍵流程（推薦）

### 新筆電的前置需求（只需要裝一次，跟這個專案無關，沒辦法用腳本繞過）

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)（只用來跑 PostgreSQL）
2. [Python 3.11](https://www.python.org/downloads/)（安裝時記得勾選 "Add python.exe to PATH"）
3. [Node.js 20+](https://nodejs.org/)
4. NVIDIA 顯示卡驅動（更新到最新 Game Ready/Studio 版本即可，RTX 4060 內建支援 CUDA 12.x）

裝完可以用 `nvidia-smi` 確認驅動有抓到顯卡。

### 複製 + 執行

1. 把整個 `peoplecount` 資料夾複製到新筆電（USB、網路磁碟、`git clone` 都可以）
2. 雙擊資料夾裡的 **`start.bat`**（它只是幫你跑
   `powershell -ExecutionPolicy Bypass -File start.ps1`，省得每次手打）。
   也可以自己打開 PowerShell 執行同一條指令。

腳本會自動依序做完:

- 用 Docker 啟動 PostgreSQL + PostGIS,並等到資料庫 ready
- 第一次執行時自動建立 `backend/.env`(複製自 `.env.example`,預設值就是內建鏡頭
  `CAMERA_SOURCE=0` + GPU `cuda:0`,不用手動改)
- 第一次執行時建立 Python venv、安裝 GPU 版 PyTorch(cu121)+ 其他套件(這步比較久,
  要下載幾百 MB)
- 第一次執行時 `npm install` 前端套件
- 開兩個新的 PowerShell 視窗分別跑 backend(uvicorn)和 frontend(vite dev server)
- 灌一組示範區域/計數線(重複執行不會重複灌,已存在就跳過)
- 自動打開瀏覽器 http://localhost:5173

**之後每次要用,只要再雙擊一次 `start.bat` 就好**——已經裝好的東西(venv、
node_modules、.env)不會重裝,已經在跑的 backend/frontend 不會重複開,是完全
可以重複執行的腳本。

### 電腦重開機後怎麼辦

**一樣雙擊 `start.bat`(或跑同一條 PowerShell 指令)就好。** 重開機後:

- `venv`、`node_modules`、`.env`、已下載的 GPU PyTorch 都還在硬碟上,**不會**
  重新安裝,這部分很快
- 但 **PostgreSQL 容器、backend、frontend 這些「正在跑的程序」都會隨著關機/
  重開機消失**,必須重新啟動——這就是 `start.bat` 存在的目的

Postgres 容器已經設定 `restart: unless-stopped`,只要 Docker Desktop 有啟動,
容器會自己重新跑起來(不用你手動 `docker compose up`);但 backend/frontend 是
一般 Windows 程序,不會自己重開,所以每次開機後還是要跑一次 `start.bat`。如果
想要開機就自動啟動,可以把 `start.bat` 的捷徑放進
`shell:startup`(Win+R 輸入這個路徑可以打開該資料夾)。

### 驗證

- 兩個彈出的 PowerShell 視窗:backend 那個應該看到 uvicorn 啟動訊息、沒有
  CUDA 相關錯誤;frontend 那個看到 vite dev server 訊息
- 瀏覽器右上角顯示「即時連線中」
- 走到鏡頭前,地圖上出現跟著移動的綠色圓點

### 常見問題

- **`start.ps1` 打不開,顯示「因為在此系統上停用指令碼執行」**:改用
  `powershell -ExecutionPolicy Bypass -File start.ps1`(只影響這次執行,不會
  更動系統原則)。
- **backend 視窗顯示 `torch.cuda.is_available()` 相關錯誤或跑起來是用 CPU
  (明顯很慢)**:先在新筆電跑 `nvidia-smi` 確認驅動正常;GPU 版 torch 是裝
  cu121(對應 CUDA 12.1+),若新筆電驅動明顯較舊,打開 `start.ps1` 把
  `--index-url https://download.pytorch.org/whl/cu121` 換成對應版本,再刪掉
  `backend\.venv` 資料夾重跑一次腳本觸發重裝。
- **backend 視窗顯示抓不到鏡頭**:多半是內建鏡頭索引不是 `0`(例如有紅外線鏡頭
  搶了索引),編輯 `backend\.env` 把 `CAMERA_SOURCE` 改成 `1` 試試,再重開
  backend 視窗(或重跑 `start.ps1`)。
- **Postgres 一直連不上**:`docker compose ps`(在 `backend` 資料夾下執行)確認
  容器狀態是 `healthy`;如果是全新安裝的 Docker Desktop,第一次啟動可能要多等
  一下。
- **想清空重來**:關掉兩個 backend/frontend 視窗,`cd backend && docker compose
  down -v`(會清空資料庫歷史資料),刪掉 `backend\.venv`、`backend\.env`、
  `frontend\node_modules`,再重跑 `start.ps1` 從頭建置。

---

## 進階選項：整套 Docker 化（改用 IP Camera 時才需要）

如果之後不用筆電內建鏡頭,改用網路攝影機(RTSP/ONVIF IP Camera),那 backend 也
不需要碰任何實體裝置了,可以整套 Docker 化(含 GPU 直通),用根目錄的
`docker-compose.yml`:

```powershell
cd peoplecount\backend
copy .env.example .env
notepad .env
# 把 CAMERA_SOURCE 改成 IP Camera 的 RTSP URL，例如：
#   CAMERA_SOURCE=rtsp://192.168.1.50:554/stream1
```

編輯根目錄 `docker-compose.yml`,把 backend 服務底下這兩行刪掉(那是給實體 USB
鏡頭 passthrough 用的,IP Camera 不需要):

```yaml
    devices:
      - /dev/video0:/dev/video0
```

確認 Docker Desktop 的 GPU passthrough 沒問題:

```powershell
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

然後建置啟動:

```powershell
cd peoplecount
docker compose build
docker compose up -d
docker compose exec backend python scripts/seed_demo.py
```

瀏覽器開 http://localhost:5173。停止/清除方式跟上面一節一樣，改用根目錄的
`docker compose down` / `down -v`。

### 常見問題(整套 Docker 化)

- **容器裡 `torch.cuda.is_available()` 是 `False`**:確認主機 `nvidia-smi`
  顯示的 CUDA 版本 >= 12.1(backend Dockerfile 裝的是 `cu121` 版 torch);驅動
  較舊就把 `backend/Dockerfile` 裡的 `--index-url` 換成對應較舊 CUDA 版本。
- **前端連不到後端**:確認根目錄 `docker-compose.yml` 的
  `frontend.build.args`(`VITE_API_BASE`/`VITE_WS_BASE`)和 `backend/.env` 的
  `CORS_ORIGINS` 都指向正確的位址。
