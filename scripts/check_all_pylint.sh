#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running pylint on all Python files in the project...${NC}"

# Find all Python files, excluding those in __pycache__ and .venv directories
FILES=$(find . -name "*.py" -not -path "*/\.*" -not -path "*/__pycache__/*" -not -path "*.venv*")

# Set the threshold score for pylint
THRESHOLD=8.0
EXIT_CODE=0
TOTAL_SCORE=0
FILE_COUNT=0

for FILE in $FILES; do
    echo -e "Checking ${YELLOW}$FILE${NC}..."
    
    # Run pylint and get the score
    PYLINT_OUTPUT=$(pylint --output-format=text "$FILE" 2>&1)
    EXIT_STATUS=$?
    
    # Extract the score from pylint output - handle both the old and new formats
    SCORE=$(echo "$PYLINT_OUTPUT" | grep "Your code has been rated at" | grep -oE '[0-9]+\.[0-9]+' | head -1)
    
    # If no score is found, there might be a syntax error
    if [ -z "$SCORE" ]; then
        echo -e "${RED}Error: Could not run pylint or get score for $FILE${NC}"
        echo "$PYLINT_OUTPUT"
        EXIT_CODE=1
        continue
    fi
    
    # Sum up total score for average calculation
    # Make sure we have a valid score before adding it
    if [[ "$SCORE" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        TOTAL_SCORE=$(echo "$TOTAL_SCORE + $SCORE" | bc -l)
        ((FILE_COUNT++))
        
        # Compare the score with the threshold
        if (( $(echo "$SCORE < $THRESHOLD" | bc -l) )); then
            echo -e "${RED}$FILE scored $SCORE/10, which is below the threshold of $THRESHOLD/10${NC}"
            echo "$PYLINT_OUTPUT" | grep -E '\[.*\]'  # Show only the errors/warnings
            EXIT_CODE=1
        else
            echo -e "${GREEN}$FILE scored $SCORE/10${NC}"
        fi
    else
        echo -e "${RED}Error: Invalid score format for $FILE${NC}"
        EXIT_CODE=1
    fi
done

# Calculate average score
if [ $FILE_COUNT -gt 0 ]; then
    AVG_SCORE=$(echo "scale=2; $TOTAL_SCORE / $FILE_COUNT" | bc -l)
    echo -e "\n${YELLOW}Average score for all files: ${GREEN}$AVG_SCORE/10${NC}"
fi

# Show overall status
if [ $EXIT_CODE -ne 0 ]; then
    echo -e "\n${RED}Some files have pylint issues that need to be fixed.${NC}"
else
    echo -e "\n${GREEN}All Python files pass the minimum pylint score of $THRESHOLD/10.${NC}"
fi

exit $EXIT_CODE
