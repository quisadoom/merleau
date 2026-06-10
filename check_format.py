import pandas as pd

def check_file(filename):
    try:
        df = pd.read_excel(filename, engine='openpyxl')
        print(f"{filename}: openpyxl success")
        return
    except Exception as e:
        pass
        
    try:
        df = pd.read_excel(filename, engine='xlrd')
        print(f"{filename}: xlrd success")
        return
    except Exception as e:
        pass
        
    try:
        df = pd.read_html(filename, encoding='utf-8')
        print(f"{filename}: html success")
        return
    except Exception as e:
        pass
        
    print(f"{filename}: Unknown format")

check_file("c:/dashboard/퐁티_1_300.xls")
