"""
重置数据库脚本（如果数据库文件损坏）
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'privacy_lbs_backend.settings')
django.setup()

from django.core.management import call_command

def reset_database():
    """重置数据库"""
    db_file = 'db_new.sqlite3'
    
    print("=" * 60)
    print("重置数据库")
    print("=" * 60)
    
    # 备份旧数据库
    if os.path.exists(db_file):
        backup_file = f'{db_file}.backup'
        print(f"\n备份数据库文件: {db_file} -> {backup_file}")
        try:
            import shutil
            shutil.copy2(db_file, backup_file)
            print(f"[OK] 备份完成")
        except Exception as e:
            print(f"[警告] 备份失败: {e}")
        
        # 删除旧数据库
        print(f"\n删除旧数据库文件: {db_file}")
        try:
            os.remove(db_file)
            print(f"[OK] 删除完成")
        except Exception as e:
            print(f"[错误] 删除失败: {e}")
            print("请手动关闭所有访问数据库的程序后重试")
            return False
    
    # 重新创建数据库
    print(f"\n重新创建数据库...")
    try:
        call_command('migrate', verbosity=1)
        print(f"[OK] 数据库创建完成")
        return True
    except Exception as e:
        print(f"[错误] 数据库创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n数据库重置工具\n")
    print("警告：这将删除所有现有数据！")
    response = input("确认继续？(yes/no): ")
    
    if response.lower() == 'yes':
        if reset_database():
            print("\n[OK] 数据库重置成功！")
        else:
            print("\n[错误] 数据库重置失败")
    else:
        print("\n操作已取消")
