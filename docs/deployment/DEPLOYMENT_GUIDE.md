# Production Deployment Guide

## ✅ Deployment Configuration Complete

Your AI Dev Agent is now configured for **production deployment** on Replit using **Autoscale mode**.

## How It Works

### Development vs Production

**Development Mode** (Current):
- Backend API runs on port 8000
- React dev server runs on port 5000 with hot module reload (HMR)
- Two separate processes for development efficiency

**Production Mode** (When Published):
- Single FastAPI server on port 5000
- Serves pre-built React static files from `frontend/dist/`
- API endpoints and frontend served from same process
- Optimized and production-ready

## Deployment Configuration

### Build Command
```bash
cd frontend && npm install && npm run build
```

**What it does:**
1. Installs all frontend dependencies
2. Compiles TypeScript to JavaScript
3. Bundles React app with Vite
4. Outputs optimized static files to `frontend/dist/`
5. Creates production-ready assets (CSS, JS bundles)

### Run Command
```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

**What it does:**
1. Starts FastAPI backend on port 5000
2. FastAPI serves both:
   - API endpoints (`/api/*`, `/health`, `/metrics`)
   - React static files from `frontend/dist/`
   - SPA routing (all other routes → `index.html`)

## How Static File Serving Works

### Route Handling in Production:

| Route Pattern | Served By | Description |
|--------------|-----------|-------------|
| `/` | `frontend/dist/index.html` | React app entry point |
| `/assets/*` | `frontend/dist/assets/*` | Static CSS/JS bundles |
| `/api/*` | FastAPI endpoints | Backend API |
| `/health` | FastAPI endpoint | Health check |
| `/metrics` | FastAPI endpoint | Prometheus metrics |
| All other routes | `frontend/dist/index.html` | SPA routing (React Router handles it) |

### Implementation Details:

1. **Static Assets Mounting:**
   ```python
   app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")))
   ```

2. **Root Route:**
   ```python
   @app.get("/", response_class=FileResponse)
   async def serve_frontend():
       return FileResponse("frontend/dist/index.html")
   ```

3. **Catch-All for SPA Routing:**
   ```python
   @app.get("/{full_path:path}", response_class=FileResponse)
   async def serve_spa_routes(full_path: str):
       # Serves index.html for all non-API routes
       # React Router handles client-side routing
   ```

## How to Deploy

### Step 1: Click "Publish" Button
1. Look for the **"Publish"** button in your Replit workspace header
2. Click it to start the deployment process

### Step 2: Wait for Build
The deployment will:
1. ✅ Run the build command (installs deps, builds React app)
2. ✅ Start the run command (starts FastAPI server)
3. ✅ Assign a public URL to your app

**Build time:** ~2-3 minutes (first deployment)

### Step 3: Access Your Live App
You'll get a public URL like:
```
https://[your-app-name].replit.app
```

## Verification Checklist

Before deploying, verify:

- ✅ Frontend built successfully: `ls -la frontend/dist/`
- ✅ Static assets exist: `ls -la frontend/dist/assets/`
- ✅ Backend serves static files: `curl http://localhost:8000/`
- ✅ API endpoints work: `curl http://localhost:8000/health`
- ✅ SPA routing works: `curl http://localhost:8000/some-route`

All checks ✅ **PASSED** - Ready to deploy!

## Testing the Deployment

### After Publishing:

1. **Test Frontend:**
   - Open your public URL
   - Should see the React UI
   - Navigate between panels (LLM Testing, GitHub, etc.)

2. **Test API:**
   - Visit: `https://[your-app].replit.app/health`
   - Should return: `{"status":"healthy"}`

3. **Test API Docs:**
   - Visit: `https://[your-app].replit.app/docs`
   - Should see FastAPI Swagger documentation

## Deployment Type: Autoscale

**Why Autoscale?**
- ✅ Automatically scales with traffic
- ✅ Scales to zero when idle (cost-effective)
- ✅ Handles HTTP/WebSocket requests
- ✅ Perfect for web applications
- ✅ Pay only for usage

**Scaling:**
- Scales up automatically under load
- Scales down to zero when idle
- Fast cold start (~1-2 seconds)

## Troubleshooting

### Issue: 404 on Frontend Routes
**Solution:** Already fixed! The catch-all route serves `index.html` for all non-API routes.

### Issue: Static Assets Not Loading
**Solution:** Already fixed! `/assets/*` is properly mounted to serve CSS/JS bundles.

### Issue: API Endpoints Return HTML
**Solution:** Already fixed! API routes are checked before catch-all route.

### Issue: Build Fails
**Possible causes:**
- Node.js version incompatibility → Check `package.json` engines
- Missing dependencies → Check `frontend/package.json`
- TypeScript errors → Run `cd frontend && npm run build` locally to debug

### Issue: App Crashes on Start
**Check:**
1. Environment variables (TOGETHER_API_KEY, etc.)
2. Database connection
3. Port configuration (should be 5000)

## Cost Estimation

**Autoscale Deployment Pricing:**
- Based on compute units and requests
- Scales to zero when idle (no cost)
- Typical usage: $5-20/month for moderate traffic
- See Replit pricing for exact rates

## Post-Deployment

### Updating the App:
1. Make changes in your workspace
2. Click "Publish" again
3. Replit will rebuild and redeploy

### Monitoring:
- Check metrics: `https://[your-app].replit.app/metrics`
- View logs in Replit Deployments pane
- Monitor performance in Replit dashboard

### Custom Domain (Optional):
1. Go to Deployments pane
2. Click "Add custom domain"
3. Follow DNS configuration steps

## Architecture Diagram

```
User Browser
     ↓
Replit CDN (if using Static Deployment)
     ↓
FastAPI Server (Port 5000)
     ├─→ /api/* → Backend API Endpoints
     ├─→ /health → Health Check
     ├─→ /metrics → Prometheus Metrics
     ├─→ /assets/* → Static Files (CSS/JS)
     └─→ /* → index.html (React SPA)
           ↓
     React Router (Client-Side Routing)
```

## Security Considerations

### Already Implemented:
- ✅ CORS configured
- ✅ No dev server in production
- ✅ Static files served efficiently
- ✅ API endpoints properly isolated

### TODO (For Production):
- [ ] Add authentication/authorization
- [ ] Implement rate limiting
- [ ] Add webhook signature validation
- [ ] Set up HTTPS (automatic with Replit)
- [ ] Configure environment-specific secrets

## Summary

✅ **Your app is ready to deploy!**

**What's configured:**
- Autoscale deployment type
- Build command: Builds React production bundle
- Run command: Serves both API and frontend
- Static file serving for React app
- SPA routing for client-side navigation
- All routes tested and working

**Next step:** Click the **"Publish"** button! 🚀
