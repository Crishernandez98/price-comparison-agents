import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict
import json
import random


class ProductData:
    def __init__(self, store, product_name, price, url):
        self.store = store
        self.product_name = product_name
        self.price = price
        self.url = url
        self.scraped_at = datetime.now()
        self.additional_info = {}

    def to_dict(self):
        return {
            'store': self.store,
            'product_name': self.product_name,
            'price': self.price,
            'url': self.url,
            'scraped_at': self.scraped_at.isoformat()
        }


class DealAnalysis:
    def __init__(self, product, is_good_deal, reasoning, avg_price, price_diff, deal_quality):
        self.product = product
        self.is_good_deal = is_good_deal
        self.reasoning = reasoning
        self.average_price = avg_price
        self.price_difference = price_diff
        self.deal_quality = deal_quality


class Report:
    def __init__(self, analyses, summary):
        self.analyses = analyses
        self.generated_at = datetime.now()
        self.summary = summary


# Agent 1: Web Scraping Agent
class ScraperAgent:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_multiple_stores(self, urls: List[str], product_query: str) -> List[ProductData]:
        print(f"\n[AGENT 1 - SCRAPER] Starting data collection for: {product_query}")
        all_products = []

        for url in urls:
            try:
                print(f"[AGENT 1] Scraping: {url}")
                products = self.scrape_store(url, product_query)
                all_products.extend(products)
                print(f"[AGENT 1] Found {len(products)} products from {url}")
            except Exception as e:
                print(f"[AGENT 1] Error scraping {url}: {str(e)}")

        print(f"[AGENT 1] ✓ Completed! Total products found: {len(all_products)}")
        return all_products

    def scrape_store(self, url: str, product_query: str) -> List[ProductData]:
        products = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Generic scraping - customize per store
            store_name = url.split('/')[2].replace('www.', '')
            
            # Try common product container patterns
            product_containers = (
                soup.find_all('div', class_=re.compile(r'product|item', re.I)) or
                soup.find_all('article') or
                soup.find_all('li', class_=re.compile(r'product|item', re.I))
            )

            for container in product_containers[:10]:  # Limit to first 10
                product = self.extract_product_info(container, store_name, url)
                if product:
                    products.append(product)

        except Exception as e:
            print(f"[AGENT 1] Scraping error: {str(e)}")

        return products

    def extract_product_info(self, container, store_name: str, source_url: str) -> ProductData:
        try:
            # Try to find product name
            name_elem = (
                container.find(['h3', 'h4', 'h2']) or
                container.find('a', class_=re.compile(r'title|name', re.I))
            )
            
            # Try to find price
            price_elem = container.find(class_=re.compile(r'price', re.I))
            
            if name_elem and price_elem:
                name = name_elem.get_text(strip=True)
                price_text = price_elem.get_text(strip=True)
                
                # Extract numeric price
                price_match = re.search(r'[\d,]+\.?\d*', price_text)
                if price_match:
                    price = float(price_match.group().replace(',', ''))
                    return ProductData(store_name, name, price, source_url)
        except:
            pass
        
        return None

    def get_mock_data(self, product_name: str) -> List[ProductData]:
        """Generate mock data for testing without actual websites"""
        print(f"\n[AGENT 1 - SCRAPER] Generating mock data for: {product_name}")
        stores = ["Amazon", "Walmart", "BestBuy", "Target", "eBay"]
        base_price = 299.99
        products = []

        for store in stores:
            variance = random.uniform(-50, 50)
            price = round(base_price + variance, 2)
            products.append(ProductData(
                store=store,
                product_name=product_name,
                price=price,
                url=f"https://{store.lower()}.com/product"
            ))

        print(f"[AGENT 1] ✓ Generated {len(products)} mock product listings")
        return products


# Agent 2: Deal Analysis Agent
class AnalyzerAgent:
    def analyze_deals(self, products: List[ProductData]) -> List[DealAnalysis]:
        print(f"\n[AGENT 2 - ANALYZER] Analyzing {len(products)} products for deals...")
        analyses = []

        if not products:
            print("[AGENT 2] No products to analyze")
            return analyses

        prices = [p.price for p in products]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)

        print(f"[AGENT 2] Price Range: ${min_price:.2f} - ${max_price:.2f} | Average: ${avg_price:.2f}")

        for product in products:
            price_diff = product.price - avg_price
            percent_diff = (price_diff / avg_price) * 100

            # Determine deal quality
            if percent_diff <= -15:
                is_good_deal = True
                deal_quality = "EXCELLENT"
                reasoning = f"Price is {abs(percent_diff):.1f}% below average - exceptional deal!"
            elif percent_diff <= -5:
                is_good_deal = True
                deal_quality = "GOOD"
                reasoning = f"Price is {abs(percent_diff):.1f}% below average - good value."
            elif percent_diff <= 5:
                is_good_deal = False
                deal_quality = "AVERAGE"
                reasoning = f"Price is close to market average ({percent_diff:.1f}%)."
            else:
                is_good_deal = False
                deal_quality = "POOR"
                reasoning = f"Price is {percent_diff:.1f}% above average - not recommended."

            analysis = DealAnalysis(
                product=product,
                is_good_deal=is_good_deal,
                reasoning=reasoning,
                avg_price=avg_price,
                price_diff=price_diff,
                deal_quality=deal_quality
            )
            analyses.append(analysis)

        good_deals = sum(1 for a in analyses if a.is_good_deal)
        print(f"[AGENT 2] ✓ Analysis complete! Found {good_deals} good deals out of {len(analyses)}")

        return analyses


# Agent 3: Report Generation Agent
class ReportAgent:
    def generate_report(self, analyses: List[DealAnalysis]) -> Report:
        print(f"\n[AGENT 3 - REPORTER] Compiling comprehensive report...")

        # Sort by price
        analyses.sort(key=lambda a: a.product.price)

        # Generate summary
        good_deals = [a for a in analyses if a.is_good_deal]
        best_deal = analyses[0] if analyses else None

        summary = (f"Analyzed {len(analyses)} listings. "
                  f"Found {len(good_deals)} good deals. "
                  f"Best price: ${best_deal.product.price:.2f} at {best_deal.product.store}.")

        report = Report(analyses=analyses, summary=summary)
        print("[AGENT 3] ✓ Report generated successfully!")
        return report

    def display_report(self, report: Report):
        print("\n" + "=" * 80)
        print("                         PRICE COMPARISON REPORT")
        print("=" * 80)
        print(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nSUMMARY: {report.summary}")
        print("=" * 80)

        print("\n📊 DETAILED ANALYSIS:\n")

        for analysis in report.analyses:
            emoji = {
                "EXCELLENT": "🔥",
                "GOOD": "✅",
                "AVERAGE": "⚠️",
                "POOR": "❌"
            }.get(analysis.deal_quality, "⚠️")

            print(f"{emoji} {analysis.product.store:.<15} | ${analysis.product.price:>8.2f} | {analysis.deal_quality:.<10}")
            print(f"   └─ {analysis.reasoning}")
            print(f"   └─ URL: {analysis.product.url}")
            print()

        print("=" * 80)
        print("\n💡 RECOMMENDATION:")
        best_deal = report.analyses[0]
        worst_price = report.analyses[-1].product.price
        savings = worst_price - best_deal.product.price
        print(f"   Buy from {best_deal.product.store} at ${best_deal.product.price:.2f}")
        print(f"   You'll save ${savings:.2f} compared to the highest price!")
        print("=" * 80 + "\n")

    def export_to_file(self, report: Report, filename: str = "price_report.txt"):
        content = f"PRICE COMPARISON REPORT - {report.generated_at}\n\n{report.summary}\n\n"
        
        for analysis in report.analyses:
            content += f"{analysis.product.store}: ${analysis.product.price:.2f} - {analysis.deal_quality}\n"
            content += f"{analysis.reasoning}\n\n"

        with open(filename, 'w') as f:
            f.write(content)
        
        print(f"[AGENT 3] Report exported to {filename}")


# Main Program
def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        MULTI-AGENT PRICE COMPARISON SYSTEM                 ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # Initialize agents
    scraper_agent = ScraperAgent()
    analyzer_agent = AnalyzerAgent()
    report_agent = ReportAgent()

    # Get user input
    product_name = input("Enter product name to search: ")
    
    use_mock = input("\nUse mock data for demo? (y/n): ").lower() == 'y'

    if use_mock:
        # Demo mode with mock data
        scraped_data = scraper_agent.get_mock_data(product_name)
    else:
        # Real scraping mode
        print("\nEnter store URLs (one per line, empty line to finish):")
        urls = []
        while True:
            url = input()
            if not url.strip():
                break
            urls.append(url)

        scraped_data = scraper_agent.scrape_multiple_stores(urls, product_name)

    if not scraped_data:
        print("\n❌ No data collected. Exiting.")
        return

    # Agent 2: Analyze deals
    analyses = analyzer_agent.analyze_deals(scraped_data)

    # Agent 3: Generate and display report
    report = report_agent.generate_report(analyses)
    report_agent.display_report(report)

    # Optional: Export to file
    export = input("Export report to file? (y/n): ").lower() == 'y'
    if export:
        report_agent.export_to_file(report)

    print("\n✓ Process complete!")


if __name__ == "__main__":
    main()