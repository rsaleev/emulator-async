import operator
import asyncio
from functools import reduce
from binascii import hexlify
from src.api.shtrih.commands import COMMANDS
from src.api.shtrih import logger 
from collections import deque


class ShtrihProto:

    ENQ = bytearray((0x05,))
    STX = bytearray((0x02,))
    ACK = bytearray((0x06,))
    NAK = bytearray((0x15,))
    PING = bytearray((0x00,))

    @classmethod
    def payload_crc_calc(cls, payload:bytearray) -> bytearray:
        return bytearray((reduce(operator.xor, payload),))

    @classmethod
    def payload_pack(cls, payload:bytearray) -> bytearray:
        output = bytearray()
        output.extend(ShtrihProto.STX)
        output.extend(payload)
        output.extend(cls.payload_crc_calc(payload))
        return output

class ShtrihProtoInterface:
    def __init__(self):
        self.buffer = deque()
        self.device = None 

    async def write(self, *args, **kwargs):
        raise NotImplementedError

    async def read(self, *args, **kwargs):
        raise NotImplementedError

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
                await logger.error(f'INPUT:{hexlify(payload, sep=":")}.Unknown bytes')
                await self.write(ShtrihProto.NAK) 
        except Exception as e:
           logger.exception(e)

    async def _ack_handle(self):
        self.buffer.popleft()
    
    async def _nak_handle(self):
        self.buffer.clear()
    
    async def _enq_handle(self):
        if self.buffer: 
            queued = self.buffer[0]
            await self.write(ShtrihProto.ACK)
            await asyncio.sleep(0.05)
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
            await logger.info(f'CRC:{hexlify(crc, sep=":")}')
            # check crc
            crc_arr = bytearray()
            crc_arr.extend(length)
            crc_arr.extend(data)
            # if crc positive
            if ShtrihProto.payload_crc_calc(crc_arr) == crc:
                await logger.info('CRC:ACCEPTED')
                await self._cmd_handle(data)
            # # if crc negative
            else:
                await logger.error('CRC:DECLINED')
                await self.write(ShtrihProto.NAK)


    async def _cmd_handle(self, payload:bytearray):
        cmd = payload[0:1]
        if cmd == bytearray((0xFF,)):
            cmd = payload[0:2]
        data = payload[len(cmd):]
        logger.debug(f'CMD:{hexlify(cmd, sep=":")} DATA:{hexlify(data, sep=":")}')
        hdlr = next((c for c in COMMANDS if cmd == c._command_code),None)
        if hdlr:
            await self.write(ShtrihProto.ACK)
            output = await hdlr.handle(data)
            payload_out = ShtrihProto.payload_pack(output)
            self.buffer.append(payload_out)
            # sleep before response
            await asyncio.sleep(0.05)
            await self.write(payload_out)
        else:
            logger.error(f"{cmd} not implemented in current build version ")
            await self.write(ShtrihProto.NAK)
             
   
           
        


           

   


 


   
