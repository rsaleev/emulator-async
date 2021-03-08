from escpos.escpos import Escpos


class PrinterProto(Escpos):
    def __init__(self):
        pass

    def qr(self, content, ec, size, model, native, center, impl):
        return super().qr(content, ec=ec, size=size, model=model, native=native, center=center, impl=impl)

    def text(self, txt):
        self.set(font=)
        txt.decode('cp1251').encode('cp866')
        return super().text(txt)

    def barcode(self, code, bc, height, width, pos, font, align_ct, function_type, check):
        return super().barcode(code, bc, height=height, width=width, pos=pos, font=font, align_ct=align_ct, function_type=function_type, check=check)

    