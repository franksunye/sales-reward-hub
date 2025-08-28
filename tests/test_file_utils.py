import unittest
import pandas as pd
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../modules')))
from modules.data_utils import get_unique_housekeeper_award_list

class TestFileUtils(unittest.TestCase):

    def setUp(self):
        # 创建一个临时 CSV 文件，仅包含标题行
        self.empty_file_path = 'test_empty_file.csv'
        with open(self.empty_file_path, 'w', encoding='utf-8') as f:
            f.write('管家(serviceHousekeeper),服务商(orgName),奖励名称\n')  # 仅写入标题行

        # 创建一个临时 CSV 文件，包含示例数据
        self.data_file_path = 'test_data_file.csv'
        with open(self.data_file_path, 'w', encoding='utf-8') as f:
            f.write('管家(serviceHousekeeper),服务商(orgName),奖励名称\n')  # 写入标题行
            f.write('Alice,Org1,Reward1\n')  # 添加一行数据
            f.write('Bob,Org2,Reward2\n')    # 添加另一行数据

    def tearDown(self):
        # 清理测试文件
        if os.path.exists(self.empty_file_path):
            os.remove(self.empty_file_path)
        if os.path.exists(self.data_file_path):
            os.remove(self.data_file_path)

    def test_get_unique_housekeeper_award_list_empty_file(self):
        # 调用函数并获取结果
        result = get_unique_housekeeper_award_list(self.empty_file_path)

        # 验证结果是否为 {}
        self.assertEqual(result, {})  # 期望返回空字典

    def test_get_unique_housekeeper_award_list_with_data(self):
        # 调用函数并获取结果
        result = get_unique_housekeeper_award_list(self.data_file_path)

        # # 打印结果
        # print(result)

        # 验证结果是否符合预期
        expected_result = {'Alice_Org1': ['Reward1'], 'Bob_Org2': ['Reward2']}  # 根据您的逻辑调整预期结果
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()

# python -m unittest discover -s tests -p "test_file_utils.py"