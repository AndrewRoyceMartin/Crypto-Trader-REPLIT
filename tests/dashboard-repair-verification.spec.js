// REPAIR: Dashboard data binding verification test
const { test, expect } = require('@playwright/test');

test('Dashboard shows bound real OKX data', async ({ page }) => {
    console.log('🔧 REPAIR VERIFICATION: Testing dashboard data binding after script fix...');
    
    // Navigate to dashboard with cache-busting
    await page.goto('http://127.0.0.1:5000/?cb=' + Date.now());
    
    // Wait for network to be idle and data to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000); // Allow time for API calls and data binding
    
    // Test 1: Check if metric elements have real data (not loading skeletons or placeholders)
    const portfolioValue = page.locator('#portfolioValue[data-metric="portfolioValue"]');
    const totalPnL = page.locator('#totalPnL[data-metric="totalPnL"]');
    const activePositions = page.locator('#activePositions[data-metric="activePositions"]');
    
    await expect(portfolioValue).toBeVisible();
    await expect(totalPnL).toBeVisible();
    await expect(activePositions).toBeVisible();
    
    // Test 2: Verify values are populated with real data
    const portfolioText = await portfolioValue.textContent();
    const pnlText = await totalPnL.textContent();
    const positionsText = await activePositions.textContent();
    
    console.log('📊 REPAIR VERIFICATION: Data values found:');
    console.log('  Portfolio Value:', portfolioText);
    console.log('  Total P&L:', pnlText);
    console.log('  Active Positions:', positionsText);
    
    // REPAIR: Verify real data (not placeholders or loading states)
    expect(portfolioText.trim()).not.toMatch(/^$|^—$|^NaN$|Loading|skeleton/i);
    expect(pnlText.trim()).not.toMatch(/^$|^—$|^NaN$|Loading|skeleton/i);
    expect(positionsText.trim()).not.toMatch(/^$|^—$|^NaN$|Loading|skeleton/i);
    
    // Test 3: Verify numeric content with expected real OKX values
    expect(portfolioText).toMatch(/\$1,?0[0-9][0-9]/); // Should be around $1093
    expect(positionsText).toMatch(/2[0-9]/); // Should be 27 active positions
    
    // Test 4: Check that loading skeletons are hidden
    const loadingSkeletons = page.locator('.loading-skeleton:visible');
    const skeletonCount = await loadingSkeletons.count();
    expect(skeletonCount).toBe(0);
    
    // Test 5: Verify dashboard status shows loaded state
    const dashboardStatus = page.locator('#dashboard-status');
    const statusText = await dashboardStatus.textContent();
    expect(statusText).toMatch(/loaded|complete|ready/i);
    
    console.log('✅ REPAIR VERIFICATION: All tests passed! Dashboard shows real OKX data.');
});