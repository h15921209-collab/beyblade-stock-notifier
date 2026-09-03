import yaml
import logging
from core.msrp import get_official_price_and_limit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ApplyMSRP")

def apply_all(config_path: str = "config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    targets = cfg.get("targets", [])
    logger.info(f"開始為全部 {len(targets)} 款商品套用「官方原價 + 10%」上限...")

    updated_count = 0
    for t in targets:
        name = t.get("name", "")
        old_price = t.get("max_price")
        official_price, new_max = get_official_price_and_limit(name, fallback_price=old_price)
        t["max_price"] = new_max
        updated_count += 1
        logger.info(f"  🌀 {name[:35]:<35} | 官方原價: NT$ {official_price:<5} ➔ 限制上限(+10%): NT$ {new_max}")

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    logger.info(f"✅ 全部 {updated_count} 款商品已全數設定為「官方原價 + 10%」！")

if __name__ == "__main__":
    apply_all()
