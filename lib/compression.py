import lzma
import lzham


def decompress(data):
    if data[:2] == b'SC':  # Supercell header
        hash_length = int.from_bytes(data[6:10], 'big')
        data = data[10 + hash_length:]

    if data[:4] == b'SCLZ':  # LZHAM compression
        dict_size = int.from_bytes(data[4:5], 'big')
        uncompressed_size = int.from_bytes(data[5:9], 'little')

        try:
            return lzham.decompress(data[9:], uncompressed_size, {'dict_size_log2': dict_size})

        except:
            return data

    else:  # LZMA compression
        adjusted_data = data[0:9] + bytes(4) + data[9:]

        try:
            return lzma.LZMADecompressor().decompress(adjusted_data)

        except:
            return data
