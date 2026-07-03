# 建置流程 (Build Guide)

## 適用情境

本機開發、除錯 YOLO 追蹤邏輯、快速迭代 UI。**建議把這個當主要工作流程**——在 Windows
上 Docker 容器要吃到本機鏡頭（USB/內建 webcam）並不容易，原生跑 Python 才是最單純
可靠的做法；GPU 也是原生裝 CUDA 版 PyTorch 最直接。只有 PostgreSQL 用 Docker。

全部 Docker 化的佈署方式（適合 IP Camera、或是要整套搬到另一台機器長期運行）請看
[DEPLOYMENT.md](DEPLOYMENT.md)。如果只是想快速把整套系統搬到另一台筆電跑起來，
不需要逐步照著做，直接用根目錄的 [start.ps1](start.ps1) 一鍵腳本即可（它做的事
就是下面這些步驟，包成一個可重複執行的腳本）。

## 前置需求

- Windows 10/11，NVIDIA 顯示卡驅動（RTX 4060，建議更新到最新 Game Ready/Studio 版本）
- Python 3.11
- Node.js 20+
- Docker Desktop（只用來跑 PostgreSQL + PostGIS；若你另外有裝好的 PostGIS 可以跳過）

## 1. 啟動資料庫

```powershell
cd peoplecount\backend
docker compose up -d
```

只會啟動 postgres 容器，並在第一次建立 volume 時自動執行 `scripts/init_db.sql` 建表。
如果之後改了 schema 要重跑 init script，得先清空 volume：`docker compose down -v`
（會清掉所有歷史資料，要注意）。

## 2. 後端環境

```powershell
cd peoplecount\backend
python -m venv .venv
.venv\Scripts\activate
```

### 2.1 先裝 GPU 版 PyTorch

務必**先裝 torch**，再裝 `requirements.txt`，避免 ultralytics 的相依解析抓到
CPU-only 版本。先用 `nvidia-smi` 確認驅動支援的 CUDA 版本（畫面右上角
`CUDA Version: xx.x`），RTX 4060 通常對應到 CUDA 12.x：

```powershell
nvidia-smi
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

安裝完務必驗證：

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

要看到 `True` 和你的顯卡名稱，才代表 GPU 有吃到；如果是 `False`，先不要往下走，
看下面「常見問題」。

### 2.2 裝其他套件

```powershell
pip install -r requirements.txt
```

### 2.3 設定環境變數

```powershell
copy .env.example .env
```

依需要調整 `.env`：

| 變數 | 說明 |
|---|---|
| `CAMERA_SOURCE` | 內建/USB 鏡頭通常是 `0`（第二顆是 `1`）；IP Camera 填 RTSP URL，例如 `rtsp://192.168.1.50:554/stream1` |
| `YOLO_DEVICE` | `cuda:0`（GPU）或 `cpu` |
| `DATABASE_URL` | 預設對應 docker-compose 的帳密，不用改 |

### 2.4 啟動後端

```powershell
uvicorn app.main:app --reload
```

啟動 log 應該看到 YOLO 權重下載/載入訊息，且沒有 CUDA 相關錯誤。開瀏覽器
http://localhost:8000/health 應該回 `{"status":"ok"}`。

### 2.5 灌示範資料（只需跑一次）

另開一個終端機：

```powershell
cd peoplecount\backend
.venv\Scripts\activate
python scripts\seed_demo.py
```

## 3. 前端環境

```powershell
cd peoplecount\frontend
npm install
npm run dev
```

開瀏覽器 http://localhost:5173，應該會看到：

- 右上角「即時連線中」（WebSocket 已連上）
- 地圖上有一個藍色區域框、一條橘色計數線（來自 `seed_demo.py`）
- 走進鏡頭畫面時，出現綠色圓點跟著你移動

## 4. 驗證清單

- [ ] `nvidia-smi` 顯示 GPU 使用率在你走動時有跳動（代表 YOLO 真的用 GPU 推論）
- [ ] 走過計數線，右側「進出計數」數字即時 +1
- [ ] 站在藍色區域內「區域即時人數」+1，離開後顯示平均停留秒數
- [ ] 在 `backend` 資料夾下 `docker compose ps` 看到 postgres 容器是 `healthy`

## 常見問題

- **`torch.cuda.is_available()` 是 `False`**：先確認 `nvidia-smi` 本身能不能跑；
  再確認裝的是 `cu121`（或對應版本）而不是預設的 CPU 版。重灌時要先
  `pip uninstall torch torchvision -y`，再重新指定 `--index-url` 安裝。
- **YOLO 抓不到鏡頭**：先用小腳本測試
  `python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"`，確認不是鏡頭
  被視訊會議軟體之類的程式佔用，或者索引值不對。
- **前端連不上 WebSocket**：確認 `backend/.env` 的 `CORS_ORIGINS` 有包含
  `http://localhost:5173`，且後端確實在跑。
- **`/health` 打不通、log 顯示連不上資料庫**：確認 `docker compose ps`
  的 postgres 容器狀態是 `healthy` 而不是還在啟動中，或是連線資訊跟 `.env` 對不上。
