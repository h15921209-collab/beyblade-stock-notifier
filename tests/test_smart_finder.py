import unittest
from core.smart_finder import (
    is_authentic_beyblade_product,
    enrich_search_query,
    BLACKLIST_KEYWORDS,
    POSITIVE_BRAND_KEYWORDS
)

class TestSmartFinder(unittest.TestCase):
    def test_blacklist_exclusions(self):
        """測試負面黑名單硬剔除（鞋類、首飾盒、3C配件、椅凳等）"""
        junk_titles = [
            "時尚雙層收納鏡面首飾盒(TO-BX07)",
            "時尚雙層收納鏡面首飾盒(TO-BX07) 粉色",
            "女鞋 Classic Platform Clog W Hdn 洞洞鞋 206750-5BX",
            "PUMA 拖鞋 男鞋 涼鞋 黑色 5BX",
            "C31N1330 電池適用(保固更久) UX32LA,UX32LN系列 BX32LA",
            "[UX20]艾瑪1.5尺手提馬鞍椅凳UX20-2501A二色可選-免運費/免組裝/椅凳",
            "四方型 19V 3.42A 65W 變壓器 TX201 S510U BX32A UX410UQ",
            "ASUS ux305充電器 w19-045n3c UX31A UX32A BX32L",
            "150W 充電器(保固更久) 適用 20V,7.5A UX580 UX550",
            "(副廠) A20-100P1A 100W TYPE-C MSI 變壓器 充電器 電源線 20V 5A ROG UX3404",
            "高品質 新款方型 變壓器 19V 2.37A 45W UX21E UX31E UX32",
            "65W USBC TYPEC 新款充電器適用 B9400CEA T303UA UX390UA",
            "C23-UX32 電池適用 UX32,UX32V,UX32VD,UX32A,BX32A",
        ]
        for title in junk_titles:
            self.assertFalse(
                is_authentic_beyblade_product(title),
                f"應該被負面黑名單硬剔除，但誤判為陀螺: {title}"
            )

    def test_legacy_generation_exclusion(self):
        """測試舊世代戰鬥陀螺（BURST 爆烈世代、舊版 B-44 等）嚴格硬剔除"""
        legacy_titles = [
            "【TAKARA TOMY】陀螺 BEYBLADE BURST#44 B-44 發射器",
            "TAKARA TOMY 戰鬥陀螺 爆烈世代 BURST B-180 滅世魔王",
            "戰鬥陀螺 超王系列 B-173 無限勇士",
            "TAKARA TOMY 戰鬥陀螺 鋼鐵奇兵 BB-10 旋風戰鬥盤",
            "TAKARA TOMY 戰鬥陀螺 BURST GT世代 B-145",
        ]
        for title in legacy_titles:
            self.assertFalse(
                is_authentic_beyblade_product(title),
                f"舊世代陀螺應嚴格排除，但誤判為 X 世代: {title}"
            )

    def test_authentic_beyblade_products(self):
        """測試正面正版戰鬥陀螺商品驗證"""
        valid_titles = [
            "TAKARATOMY BEYBLADE X 戰鬥陀螺 X BX-07 極限激戰初始組 戰鬥盤 陀螺",
            "TAKARATOMY BEYBLADE X 戰鬥陀螺 X世代 BXG-04 銀牙烈虎S 陀螺",
            "Takara Tomy Beyblade 戰鬥陀螺 X 世代 UX-20 榮耀女武神 陀螺",
            "UX-20 榮耀女武神",
            "UX-17 隕星龍騎士",
            "BX-23 鳳凰飛翼 豪華組",
            "戰鬥陀螺X BX-50 天堂日輪 0-80DS 隨機強化包Vol.11 BX-50",
            "TAKARATOMY BEYBLADE X 戰鬥陀螺X BX-28 旋風發射器 右迴旋(白色) 陀螺",
            "BX-25 戰鬥陀螺X專業收納包",
            "Takara Tomy Beyblade X 戰鬥陀螺 UX-03 魔導神杖 陀螺",
            "BEYBLADE X 戰鬥陀螺 BX-35 隨機強化組Vol.04 (台版)",
        ]
        for title in valid_titles:
            self.assertTrue(
                is_authentic_beyblade_product(title),
                f"正版戰鬥陀螺應判定為真，但誤判為假: {title}"
            )

    def test_target_model_matching(self):
        """測試目標型號比對機制（防止搜尋 BX-07 時帶入 BX-23 或非該型號產品）"""
        title_bx07 = "TAKARATOMY BEYBLADE X 戰鬥陀螺 X BX-07 極限激戰初始組 戰鬥盤 陀螺"
        title_bx23 = "TAKARATOMY BEYBLADE X 戰鬥陀螺X 世代 BX-23 鳳凰飛翼 陀螺"
        title_box = "時尚雙層收納鏡面首飾盒(TO-BX07)"

        # 搜尋 BX-07
        self.assertTrue(is_authentic_beyblade_product(title_bx07, target_keyword="BX-07"))
        self.assertTrue(is_authentic_beyblade_product(title_bx07, target_keyword="BX07"))
        self.assertFalse(is_authentic_beyblade_product(title_bx23, target_keyword="BX-07"))
        self.assertFalse(is_authentic_beyblade_product(title_box, target_keyword="BX-07"))

        # 搜尋 UX-20
        title_ux20 = "Takara Tomy Beyblade 戰鬥陀螺 X 世代 UX-20 榮耀女武神 陀螺"
        self.assertTrue(is_authentic_beyblade_product(title_ux20, target_keyword="UX-20"))
        self.assertFalse(is_authentic_beyblade_product(title_bx07, target_keyword="UX-20"))

    def test_enrich_search_query(self):
        """測試搜尋詞自動擴增（加掛 BEYBLADE X 前綴）"""
        self.assertEqual(enrich_search_query("BX-07"), "BEYBLADE X BX-07")
        self.assertEqual(enrich_search_query("UX-20"), "BEYBLADE X UX-20")
        self.assertEqual(enrich_search_query("魔導神杖"), "BEYBLADE X 魔導神杖")
        self.assertEqual(enrich_search_query("BEYBLADE X BX-35"), "BEYBLADE X BX-35")
        self.assertEqual(enrich_search_query("戰鬥陀螺 BX-23"), "戰鬥陀螺 BX-23")

if __name__ == "__main__":
    unittest.main()
