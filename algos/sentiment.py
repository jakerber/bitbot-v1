"""Sentiment analyzer used to determine if a phrase is positive or negative."""
import nltk
import string, random, re, time

TRAIN_VS_TEST = 0.8  # percentage of data to use to train- rest will be for testing
MODEL_ACCURACY_THRESHOLD = 0.9
BLOCK_START_TIME = None

def _timeBlock(description=None):
    """Track and display execution time of block of code."""
    global BLOCK_START_TIME

    # determine time previous block took to execute
    if not BLOCK_START_TIME:
        BLOCK_START_TIME = time.time()
    else:
        currentTime = time.time()
        prevBlockExecutionTime = currentTime - BLOCK_START_TIME
        print("\tdone (%is)" % prevBlockExecutionTime)
        BLOCK_START_TIME = currentTime

    # print description
    if description:
        print("%s..." % description)


class SentimentAnalyzer:
    """SentimentAnalyzer object."""
    def __init__(self):
        self.model = None
        self.positiveSentimentIndicator = "Positive"
        self.negativeSentimentIndicator = "Negative"
        self.positiveTweetsInputFile = "positive_tweets.json"
        self.negativeTweetsInputFile = "negative_tweets.json"

        # generate model upon initialization
        self.generate()

    def cleanWords(self, words):
        """Filter out insignificant words from a list."""
        stopWords = nltk.corpus.stopwords.words("english")
        cleanedWords = []

        # determine tag (noun, verb, or adjective) for lemmatizer
        for word, tag in nltk.tag.pos_tag(words):

            # remove non-word characters from words
            word = re.sub("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|"\
                           "(?:%[0-9a-fA-F][0-9a-fA-F]))+", "", word)
            word = re.sub("(@[A-Za-z0-9_]+)", "", word)

            # convert from nltk tag to nltk.stem.wordnet tag identifiers
            pos = "a"
            if tag.startswith("NN"):
                pos = "n"
            elif tag.startswith("VB"):
                pos = "v"

            # group words together using wordnet lemmatizer
            # e.g. "dog" and "dogs" will both be grouped into "dog"
            lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
            word = lemmatizer.lemmatize(word, pos)

            # use word if anything left after removing non-word characters
            if len(word) > 0 and word not in string.punctuation and word.lower() not in stopWords:
                cleanedWords.append(word.lower())

        return cleanedWords

    def isPositive(self, phrase):
        """Determine if the sentiment of a phrase is positive or negative."""
        tokens = self.cleanWords(nltk.tokenize.word_tokenize(phrase))
        tokensForModel = self._tokenListToNBCDict(tokens)  # nltk.NaiveBayesClassifier compatible
        sentiment = self.model.classify(tokensForModel)
        return sentiment == self.positiveSentimentIndicator

    def generate(self):
        """Generate a sentiment model."""
        print("*** generating sentiment model")

        # download required NLTK packages
        _timeBlock("downloading required NLTK packages")
        nltk.download("stopwords")
        nltk.download("averaged_perceptron_tagger")
        nltk.download("wordnet")
        nltk.download("punkt")

        # tokenize training data
        _timeBlock("tokenizing positive tweets")
        posTweetTokens = nltk.corpus.twitter_samples.tokenized(self.positiveTweetsInputFile)
        posCleanedTokens = [self.cleanWords(tokens) for tokens in posTweetTokens]
        _timeBlock("tokenizing negative tweets")
        negTweetTokens = nltk.corpus.twitter_samples.tokenized(self.negativeTweetsInputFile)
        negCleanedTokens = [self.cleanWords(tokens) for tokens in negTweetTokens]

        # generate dataset from tokens
        _timeBlock("generating datasets")
        positiveDataset = [(self._tokenListToNBCDict(tokens), self.positiveSentimentIndicator)
                           for tokens in posCleanedTokens]
        negativeDataset = [(self._tokenListToNBCDict(tokens), self.negativeSentimentIndicator)
                           for tokens in negCleanedTokens]
        dataset = positiveDataset + negativeDataset

        # train model
        _timeBlock("training model")
        random.shuffle(dataset)
        trainingIndex = int(len(dataset) * TRAIN_VS_TEST)
        trainData = dataset[:trainingIndex]
        self.model = nltk.NaiveBayesClassifier.train(trainData)

        # determine accuracy
        _timeBlock("determining accurancy")
        testData = dataset[trainingIndex:]
        accuracy = nltk.classify.accuracy(self.model, testData)
        print("accuracy is: %f" % accuracy)
        if accuracy < MODEL_ACCURACY_THRESHOLD:
            raise RuntimeError("sentiment model is not accurate enough")

        # display success
        _timeBlock()
        print("*** sentiment model generated!")

    def _tokenListToNBCDict(self, tokenList):
        """Convert list of tokens to nltk.NaiveBayesClassifier token dictionary."""
        return {token: True for token in tokenList}

if __name__ == "__main__":
    x = SentimentAnalyzer()
    x.isPositive("this is so bad")
