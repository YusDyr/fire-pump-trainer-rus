package ru.ekstremum.ncpk;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.content.res.Configuration;
import android.view.WindowManager;
import android.view.View;
import android.view.Window;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;

public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Window w = getWindow();
        w.setStatusBarColor(Color.parseColor("#14181b"));
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#e3e6e8"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setTextZoom(100);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setSupportZoom(true);
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String url) {
                return !url.startsWith("file:///android_asset/");
            }
        });
        setContentView(web);
        applyFullscreen(getResources().getConfiguration());
        if (state != null) web.restoreState(state);
        else web.loadUrl("file:///android_asset/index.html");
    }

    private void applyFullscreen(Configuration c) {
        Window w = getWindow();
        View d = w.getDecorView();
        if (c.orientation == Configuration.ORIENTATION_LANDSCAPE) {
            w.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
            d.setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        } else {
            w.clearFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
            d.setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        }
    }

    @Override
    public void onConfigurationChanged(Configuration c) {
        super.onConfigurationChanged(c);
        applyFullscreen(c);
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onPause() { super.onPause(); web.evaluateJavascript("try{window.__ncpkBg&&window.__ncpkBg(true)}catch(e){}", null); web.onPause(); web.pauseTimers(); }

    @Override
    protected void onResume() { super.onResume(); web.resumeTimers(); web.onResume(); web.evaluateJavascript("try{window.__ncpkBg&&window.__ncpkBg(false)}catch(e){}", null); }

    @Override
    public void onBackPressed() {
        web.evaluateJavascript("(function(){var m=document.getElementById('plateModal');if(m&&!m.hidden){m.hidden=true;return '1'}return '0'})()",
            new android.webkit.ValueCallback<String>() {
                @Override public void onReceiveValue(String r) {
                    if (!"\"1\"".equals(r)) MainActivity.super.onBackPressed();
                }
            });
    }
}
