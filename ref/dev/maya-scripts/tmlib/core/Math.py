def subtract_vector_array(inputA, inputB):
    return_tuple = []

    if len(inputA) != len(inputB):
        raise Exception("Input A length not qual input B")

    for i in range(len(inputA)):
        posA = inputA[i]
        posB = inputB[i]

        pos_result = []

        for j in range(3):
            pos_result.append(posA[j] - posB[j])

        return_tuple.append(pos_result)

    return tuple(return_tuple)


def add_vector_array(inputA, inputB):
    return_tuple = []

    if len(inputA) != len(inputB):
        raise Exception("Input A length not qual input B")

    for i in range(len(inputA)):
        posA = inputA[i]
        posB = inputB[i]
        
        return_tuple.append(add_vector(posA,posB))


    return tuple(return_tuple)

def subtract_vector_array(inputA, inputB):
    return_tuple = []

    if len(inputA) != len(inputB):
        raise Exception("Input A length not qual input B")

    for i in range(len(inputA)):
        posA = inputA[i]
        posB = inputB[i]

        return_tuple.append(subtract_vector(posA,posB))

    return tuple(return_tuple)


def add_vector(inputA, inputB):
    pos_result = []

    for j in range(3):
        pos_result.append(inputA[j] + inputB[j])

    return pos_result

def subtract_vector(inputA, inputB):
    pos_result = []

    for j in range(3):
        pos_result.append(inputA[j] - inputB[j])

    return pos_result

