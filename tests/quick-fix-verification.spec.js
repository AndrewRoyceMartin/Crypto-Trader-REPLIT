// REPAIR: Quick Playwright test to verify dashboard data binding fixes
const { test, expect } = require('@playwright/test');

test('Dashboard data binding verification', async ({ page }) => {
    console.log('🔧 REPAIR VERIFICATION: Testing dashboard data binding fixes...');
    
    // Navigate to dashboard
    await page.goto('http://127.0.0.1:5000/');
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Test 1: Check if metric elements exist
    const portfolioValue = page.locator('#portfolioValue[data-metric="portfolioValue"]');
    const totalPnL = page.locator('#totalPnL[data-metric="totalPnL"]');
    const activePositions = page.locator('#activePositions[data-metric="activePositions"]');
    
    await expect(portfolioValue).toBeVisible();
    await expect(totalPnL).toBeVisible();
    await expect(activePositions).toBeVisible();
    
    // Test 2: Check if data is loaded (not showing loading skeletons)
    const loadingSkeletons = page.locator('.loading-skeleton:visible');
    await expect(loadingSkeletons).toHaveCount(0, { timeout: 10000 });
    
    // Test 3: Check if values are populated (not empty or showing '—')
    const portfolioText = await portfolioValue.textContent();
    const pnlText = await totalPnL.textContent();
    const positionsText = await activePositions.textContent();
    
    console.log('📊 Data values found:');
    console.log('  Portfolio Value:', portfolioText);
    console.log('  Total P&L:', pnlText);
    console.log('  Active Positions:', positionsText);
    
    // Verify values are not placeholder
    expect(portfolioText).not.toBe('—');
    expect(pnlText).not.toBe('—');
    expect(positionsText).not.toBe('—');
    
    // Test 4: Check for numeric content (currency or numbers)
    expect(portfolioText).toMatch(/\$[\d,]+/); // Should contain currency format
    expect(positionsText).toMatch(/\d+/); // Should contain numbers
    
    // Test 5: Verify stable data attributes are present
    await expect(page.locator('[data-metric-card="portfolio"]')).toBeVisible();
    await expect(page.locator('[data-metric-card="pnl"]')).toBeVisible();
    await expect(page.locator('[data-metric-card="positions"]')).toBeVisible();
    
    console.log('✅ REPAIR VERIFICATION: All tests passed! Dashboard data binding is working correctly.');
});