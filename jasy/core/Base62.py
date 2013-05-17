#
# Jasy - Web Tooling Framework
# Copyright 2013 Sebastian Fastner
# Copyright 2013 Sebastian Werner
#

base62Table = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
base62InvertedTable = {}

i = 0
while i < 62:
    base62InvertedTable[base62Table[i]] = i
    i += 1

# And mask for 6, 6, 6, 5, 4, 3, 2, 1 leading bits
bitMask = [252, 252, 252, 248, 240, 224, 192, 128] 

def encodeArrayOfBytes(arr):
    # This works like a bit register. Take first 6 bits and append it to result. Take next 6 bits and so on.
    # A special case is if the 6 bits represents 60, 61, 62 or 63. In this case one more bit is used to
    # reduce 6 bit (= 64 different values) by two values.
    result = []
    charLength = arr.length
    bitLength = charLength * 8
    bitPos = 0
    specialBit = null

    while bitPos < bitLength:
        charOffset = bitPos / 8 | 0
        bitOffset = bitPos % 8
    
        if charOffset + 1 >= charLength:
            
            # Special case : no more next char so no more bits
            remainingBits = bitLength - bitPos
            
            if remainingBits >= 6:
                moveRight = 2
            else:
                moveRight = 8 - remainingBits
            
            extractedBits = ( (arr[charOffset] << bitOffset) & 252 ) >> moveRight
        
        else:
            leftoverBits = bitOffset - 2
            extractedBits = (( (arr[charOffset] << bitOffset) & bitMask[bitOffset] ) + ( (arr[charOffset+1] & bitMask[8-leftoverBits]) >> (6-leftoverBits) )) >> 2
    
        if (extractedBits & 62) == 60:
            extractedBits = 61
            bitPos -= 1

        elif (extractedBits & 62) == 62:
            extractedBits = 62
            bitPos -= 1
        
        result.append(extractedBits)
        bitPos += 6

    return result


def decodeToArrayOfBytes(arr):
    result = []
    current = 0
    bitOffset = 0
    charOffset = 0
    charLength = arr.length

    charOffset=0
    while charOffset < charLength:
        char = arr[charOffset]
    
        bitsNeeded = 8 - bitOffset
        if char == 61 or char == 62:

            correctBits = 30 if char == 61 else 31

            if bitsNeeded <= 5:
                current = ((current << bitsNeeded) + (correctBits >> (5-bitsNeeded))) & 255
                result.append(current)
                current = (((correctBits << bitsNeeded) & 255) >> bitsNeeded) & 63
                bitOffset = 5 - bitsNeeded
            else:
                current = (current << 5) + correctBits
                bitOffset += 5
            
                if bitOffset == 8:
                    result.append(current)
                    current = 0
        else:
            if bitsNeeded <= 6:
                last = charOffset == charLength -1
                charShift = char
                if not last:
                    charShift = char >> (6-bitsNeeded)
                
                current = ((current << bitsNeeded) + charShift) & 255
                result.append(current)
                
                if not last:
                    current = (((char << bitsNeeded) & 255) >> bitsNeeded) & 63
                
                bitOffset = 6 - bitsNeeded
            
            else:
                current = (current << 6) + char
                bitOffset += 6
            
                if bitOffset == 8:
                    result.append(current)
                    current = 0

        charOffset += 1

    return result


def encodeArrayToString(arr):
    result = encodeArrayOfBytes(arr)

    i = 0
    ii = result.length
    while i < ii:
        result[i] = base62Table[result[i]]
        i += 1
    
    return "".join(result)


def decodeStringToArray(str):
    len = len(str)
    byteArray = []

    i = 0
    while i<len:
        byteArray[i] = base62InvertedTable[str[i]]
        i += 1

    return decodeToArrayOfBytes(byteArray)

