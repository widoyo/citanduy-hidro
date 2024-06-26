import sys

def main(filename):
    try:
        nama_pos, tahun = filename.split('.')[0].split('_')
    except:
        print('\nPenggunaan:\n  Nama file WAJIB <namalokasi>_<tahun>.csv\n\n')
        return
    try:
        lines = open(filename)
    except:
        print('\nGagal membuka file '+filename+'\n\n')
        return
    
    lines = open(filename).readlines()
    bln = dict([(i, []) for i in range(1,13)])
    for l in lines:
        c = l.strip().split('\t')
        for i in bln.keys():
            try:
                ch = float(c[i-1].replace(',', '.'))
                bln[i].append(ch)
            except:
                pass
    with open(nama_pos + '_' + tahun + '_out.csv', 'w') as f:
        for k, v in bln.items():
            sampling = tahun + '-' + str(k)
            for i in range(len(v)):
                ch = v[i]
                f.write(nama_pos + '\t{}\t{}\n'.format(sampling + '-' + str(i+1), ch))
    
    
if __name__ == '__main__':
    try:
        params = sys.argv[1]
    except:
        print('\nPenggunaan:\n  '+sys.argv[0]+' <namalokasi>_<tahun>.csv\n\n')
        exit()
    main(params)