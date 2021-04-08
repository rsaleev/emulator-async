from asyncio.unix_events import AbstractChildWatcher
import operator
from functools import reduce
import asyncio
from binascii import hexlify
from src.api.shtrih.commands import COMMANDS
from src.api.shtrih import logger 
class ShtrihProto:

    ENQ = bytearray((0x05,))
    STX = bytearray((0x02,))
    ACK = bytearray((0x06,))
    NAK = bytearray((0x15,))
    PING = bytearray((0x00,))

    def __init__(self):
        self.buffer = asyncio.Queue()
        self.device = None 

    async def write(self, *args, **kwargs):
        raise NotImplementedError

    async def read(self, *args, **kwargs):
        raise NotImplementedError

    def crc_calc(self, payload:bytearray) -> bytearray:
        return bytearray((reduce(operator.xor, payload),))


    async def _transmit(self, arr:bytearray):
        output = bytearray()
        output.extend(ShtrihProto.STX)
        output.extend(arr)
        output.extend(self.crc_calc(arr))
        await self.write(output)
       

    async def consume(self):
        try:
            payload = await self.read(1)
            if payload == ShtrihProto.ENQ:
                await self._enq_handle()
            elif payload == ShtrihProto.ACK:
                await self._ack_handle()
            elif payload == ShtrihProto.STX:
                await self._stx_handle()
            elif payload == ShtrihProto.NAK:
                await self._nak_handle()
            else:
                await self.write(ShtrihProto.NAK) 
                await logger.error(f'INPUT:{hexlify(payload, sep=":")}.Unknown byte controls ')
        except Exception as e:
            await logger.exception(e)


    async def _ack_handle(self):
        while not self.buffer.empty(): 
            await self.buffer.get() 
    
    async def _nak_handle(self):
        while not self.buffer.empty(): 
            await self.buffer.get() 
    
    async def _enq_handle(self):
        if not self.buffer.empty(): 
            queued = await self.buffer.get()
            await self.write(ShtrihProto.ACK)
            await self.write(queued) 
        else:
            await self.write(ShtrihProto.NAK)

    async def _stx_handle(self): 
        length = await self.read(1) 
        await logger.debug(f'LEN:{hexlify(length, sep=":")}')
        # read bytes: total bytes size = length
        data = await self.read(length[0]) 
        await logger.debug(f'DATA:{hexlify(data, sep=":")}')
        # check if data presented
        if not data:
            # if data not presented in payload 
            await self.write(ShtrihProto.NAK) 
        # # if data presented in payload
        else:
            crc = await self.read(1) 
            await logger.debug(f'CRC:{hexlify(crc, sep=":")}')
            # check crc
            crc_arr = bytearray()
            crc_arr.extend(length)
            crc_arr.extend(data)
            # if crc positive
            if self.crc_calc(crc_arr) == crc:
                await logger.debug('CRC:ACCEPTED')
                await self._cmd_handle(data)
            # # if crc negative
            else:
                await logger.debug('CRC:DECLINED')
                await self.write(ShtrihProto.NAK) 

    async def _cmd_handle(self, payload:bytearray):
        cmd = payload[0:1]
        if cmd == bytearray((0xFF,)):
            cmd = payload[0:2]
        data = payload[len(cmd):]
        await logger.debug(f'CMD:{hexlify(cmd, sep=":")} DATA:{hexlify(data, sep=":")}')
        hdlr = next((c for c in COMMANDS if cmd == c._command_code),None)
        if hdlr:
            await self.write(ShtrihProto.ACK)
            output,_ = await hdlr.handle()
            await asyncio.gather(self._transmit(output), self.buffer.put(output))
        else:
            await asyncio.gather(self.write(ShtrihProto.NAK),logger.error(f"{cmd} not implemented in current build version "))
             
   
           
        


           

   


 


   