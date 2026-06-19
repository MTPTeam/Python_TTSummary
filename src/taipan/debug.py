import pkg_resources

"""installed_packages = pkg_resources.working_set
for package in installed_packages:
    print(f"{package.key}=={package.version}")
"""

### do they match 



def compare_hastus_files(path1, path2):
    with open(path1, 'r') as f1, open(path2, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
    
    if lines1 == lines2:
        print("Files are identical")
        return True
    
    differences = []
    for i, (l1, l2) in enumerate(zip(lines1, lines2), start=1):
        if l1 != l2:
            differences.append((i, l1.strip(), l2.strip()))
    
    if len(lines1) != len(lines2):
        print(f"Files have different line counts: {len(lines1)} vs {len(lines2)}")
    
    print(f"{len(differences)} differing lines:")
    for linenum, l1, l2 in differences:
        print(f"  Line {linenum}:")
        print(f"    File 1: {l1}")
        print(f"    File 2: {l2}")
    
    return False


if __name__ == "__main__":
    from tkinter import Tk
    from tkinter.filedialog import askopenfilename

    Tk().withdraw()
    print("Select first file")
    path1 = askopenfilename()
    print("Select second file")
    path2 = askopenfilename()

    compare_hastus_files(path1, path2)




