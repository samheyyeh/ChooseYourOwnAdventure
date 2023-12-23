import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Input,
  VStack,
  useToast,
  Text,
  Container,
  Skeleton,
  SkeletonText,
  Image,
  Kbd,
  Button,
} from '@chakra-ui/react';

const TextAndImageGenerator = () => {
  const [prompt, setPrompt] = useState('');

  const [scenario, setScenario] = useState('');
  const [images, setImages] 	= useState([]);
  const [question, setQuestion] = useState('');
  const [choices, setChoices] 	= useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const inputRef = useRef(null);
  const [choice, setChoice] = useState('');

  // Store context
  const [oldScenarios, setOldScenarios] = useState([]);
  const [oldQuestions, setOldQuestions] = useState([]);
  const [oldChoices, setOldChoices] = useState([]);

  useEffect(() => {
    handleWork("")
  }, []);

  const handleButtonClick = (myChoice) => {
    setChoice(myChoice);
    handleWork(myChoice);
  }

  const handleSubmit = async (e) => {
    if (e)
      e.preventDefault();
    if (isLoading) return; // Prevent spamming

    handleWork("");
  }

  const handleWork = async (myChoice) => {
    setIsLoading(true);
    setScenario('');
    setImages([]);
//    setQuestion('');
//    setChoices([]);

    try {
      console.log(`scenario ${scenario}`);
      console.log(`question ${question}`);
      console.log(`choice ${myChoice}`);
      const response = await fetch('http://127.0.0.1:5000/generate-text-and-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(
          {
           'choice':	    myChoice,
           'oldScenarios':  oldScenarios,
           'oldQuestions':  oldQuestions,
           'oldChoices':    oldChoices,
          }
        ),
      });

      if (!response.ok) {
        throw new Error("Server error, please try again.");
      }

      const result = await response.json();

      setScenario(result.data.scenario);
      setImages(result.data.images);
      setQuestion(result.data.question);
      setChoices(result.data.choices);

      setOldScenarios(result.data.oldScenarios);
      setOldQuestions(result.data.oldQuestions);
      setOldChoices(result.data.oldChoices);

    } catch (error) {
      toast({
        title: "Error",
        description: `${error.message} If this persists, please retry.`,
        status: "error",
        duration: 9000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Container centerContent py="12" maxW={"2xl"} pt={24} minH={"100vh"}>
      <VStack spacing="8">
        <VStack spacing="4" width="full">
          {isLoading ? (
            <>
              <SkeletonText mt="4" noOfLines="4" skeletonHeight="4"/>
            </>
          ) : (
            <Box width="full">
              <Text fontSize="4xl">
              {scenario}
              </Text>
            </Box>
          )}
          {isLoading ? (
            <>
              <Skeleton height="1024px" width="full" />
            </>
          ) : (
            images.map((image, index) => (
              <Box width="full">
                <Image src={`data:image/png;base64,${image}`} alt={`Generated Image ${index + 1}`} />
              </Box>
            ))
          )}
          {isLoading ? (
            <>
              <SkeletonText mt="4" noOfLines="4" skeletonHeight="4" />
            </>
          ) : (
            <Box width="full">
              <Text fontSize="4xl">{question}</Text>
            </Box>
          )}
          {isLoading ? (
            <>
              <SkeletonText mt="4" noOfLines="4" skeletonHeight="4"/>
            </>
          ) : (
            choices.map((choice, index) => (
              <Box width="full">
                <Button colorScheme='blue' size='lg' onClick={() => handleButtonClick(choice)}>{choice}</Button>
              </Box>
            ))
          )}
        </VStack>
      </VStack>
    </Container>
  );
};

export default TextAndImageGenerator;
