import operator
from functools import reduce



class ShtrihProto:


    ENQ = bytearray((0x05,))
    STX = bytearray((0x02,))
    ACK = bytearray((0x06,))
    NAK = bytearray((0x15,))
    PING = bytearray((0x00,))
   
    @classmethod
    def crc_calc(cls, payload:bytearray) -> bytearray:
        """crc_calc [summary]

        [extended_summary]

        Args:
            payload (bytearray): [description]

        Returns:
            bytearray: [description]
        """
        return bytearray((reduce(operator.xor, payload),))


    # @classmethod
    # def handle(cls, payload:bytearray) -> Union[bytearray, None]:
    #     """process [summary]

    #     [extended_summary]

    #     Args:
    #         payload (bytearray): [description]
    #     """

    #     length = payload[1:2]
    #     cmd = payload[2:3]
    #     if cmd == bytearray(0xFF):
    #         cmd = payload[2:4]
    #     data = payload[len(length)+len(cmd):-1]
    #     cmd_handler = next((handler for handler in COMMANDS if handler._command_code == cmd), None)
    #     if cmd_handler:
    #         output = cls.STX
    #         output.extend(cmd_handler.handle(data))
    #         output.extend(cls.crc_calc(output))
    #         return output
    #     else:
    #         return None
       




   
           
        


           

   


 


   