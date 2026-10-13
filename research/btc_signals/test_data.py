import csv, hashlib, io, unittest, zipfile
from data import parse_archive

def sample(ts=1704067200000):
    return [ts, '100', '110', '90', '105', '10', ts+3599999, '1000', '12', '6', '600', '0']

def packed(rows):
    out=io.BytesIO(); text=io.StringIO(); csv.writer(text).writerows(rows)
    with zipfile.ZipFile(out,'w') as z: z.writestr('BTCUSDT-1h-2024-01.csv',text.getvalue())
    raw=out.getvalue(); return raw,hashlib.sha256(raw).hexdigest()

class DataTests(unittest.TestCase):
    def test_milliseconds(self):
        raw,sha=packed([sample()]); rows=parse_archive(raw,sha)
        self.assertEqual(rows[0]['time'],1704067200)
    def test_microseconds(self):
        row=sample(1735689600000000);row[6]=row[0]+3599999999
        raw,sha=packed([row]); self.assertEqual(parse_archive(raw,sha)[0]['time'],1735689600)
    def test_bad_checksum(self):
        raw,_=packed([sample()])
        with self.assertRaises(ValueError): parse_archive(raw,'0'*64)
    def test_invalid_ohlc(self):
        row=sample();row[2]='99';raw,sha=packed([row])
        with self.assertRaises(ValueError): parse_archive(raw,sha)
    def test_nan_price(self):
        row=sample();row[4]='NaN';raw,sha=packed([row])
        with self.assertRaises(ValueError): parse_archive(raw,sha)
    def test_duplicate(self):
        row=sample();raw,sha=packed([row,row])
        with self.assertRaises(ValueError): parse_archive(raw,sha)
    def test_invalid_taker(self):
        row=sample();row[9]='11';raw,sha=packed([row])
        with self.assertRaises(ValueError): parse_archive(raw,sha)
if __name__=='__main__': unittest.main()
