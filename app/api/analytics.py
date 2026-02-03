from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.core.analytics import get_analytics_dashboard
from app.core.security import get_api_key
import time

router = APIRouter()

@router.get("/analytics/dashboard")
async def get_dashboard(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Get comprehensive analytics dashboard"""
    try:
        dashboard_data = get_analytics_dashboard()
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@router.get("/analytics/realtime")
async def get_realtime_stats(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Get real-time statistics"""
    try:
        from app.core.analytics import analytics
        stats = analytics.get_real_time_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real-time stats error: {str(e)}")

@router.get("/analytics/intel")
async def get_intel_summary(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Get extracted intelligence summary"""
    try:
        from app.core.analytics import analytics
        intel = analytics.get_extracted_intel_summary()
        return {
            "success": True,
            "data": intel,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intel summary error: {str(e)}")

@router.get("/analytics/performance")
async def get_performance_metrics(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Get performance metrics"""
    try:
        from app.core.analytics import analytics
        performance = analytics.get_performance_metrics()
        return {
            "success": True,
            "data": performance,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance metrics error: {str(e)}")

@router.get("/analytics/trending")
async def get_trending_analysis(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Get trending analysis"""
    try:
        from app.core.analytics import analytics
        trending = analytics.get_trending_analysis()
        return {
            "success": True,
            "data": trending,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trending analysis error: {str(e)}")

@router.get("/analytics/export")
async def export_analytics(format: str = "json", api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Export analytics data"""
    try:
        from app.core.analytics import analytics
        export_data = analytics.export_analytics(format)
        return {
            "success": True,
            "data": export_data,
            "format": format,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
