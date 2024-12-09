#! /usr/bin/python3

import sys,glob,subprocess, os.path

testDataPath = "TestData"

testData = [(name+".owl", name+"-subsumers.txt") for name in 
            [file [:-4] for file in glob.glob("*.owl",root_dir=testDataPath)]
            ]

print(testData)

def testReasoner(reasonerPythonFile):

    results = []

    outputfile=open("output.out", mode='a')


    for (ontologyFile, subsumersFile) in testData:

        print(file=outputfile)

        print(ontologyFile)

        full_path = os.path.abspath(testDataPath+"/"+ontologyFile)

        completed = subprocess.run(["python", reasonerPythonFile, full_path, "A"], capture_output=True, timeout=60)

        outputLines = set([line.strip() for line in completed.stdout.decode("utf-8").split("\n")])

        print()
        print("Output:")
        print()
        for line in outputLines:
            print(line, )

        if "" in outputLines:
            outputLines.remove("")

        print("Output list: "+str(outputLines))
        print()
        print("Errors:")
        print(completed.stderr.decode("utf-8"))
        print()

        with open(testDataPath+"/"+subsumersFile) as file:
            expectedSubsumers = set([line.strip() for line in file.readlines()])

        if "" in expectedSubsumers:
            expectedSubsumers.remove("")

        print("Expected: "+str(expectedSubsumers))

        success = str(outputLines==expectedSubsumers)

        print(ontologyFile+" "+ success)#)

        results.append((ontologyFile,success))

    results.sort(key = lambda x : x[0])

    print("filename", end=" ")
    for result in results:
        print(result[0], end=" ")
    print()
    
    print(reasonerPythonFile+" ")
    for result in results:
        print(result[1], end=" ")
    print()

    outputfile.close()


reasoner = sys.argv[1]

testReasoner(reasoner)
