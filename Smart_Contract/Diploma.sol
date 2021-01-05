pragma solidity >=0.4.22 <0.6.0;

/// @title John Jay College Diploma Candidates.

contract JJay {
    struct MerkleRoot {
        uint256 hash;
    }

    struct Semester {
        uint256 semester;
    }

    address owner;

    mapping(uint256 => uint256) root2sem;
    mapping(uint256 => uint256) sem2root;

    event diplomaInfo(
        uint256 hash,
        uint256 semester
    );

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner {
        require(
            msg.sender == owner,
            "Sender not authorized."
        );
        _;
    }

    function addSemester(uint256 mr, uint256 sem) public onlyOwner {
        require(
            mr > 0 && sem > 0,
            "Value of hash and semester has to be greater than 0."
            );

        require(
            root2sem[mr] == 0,
            "The semester was already added."
        );

        root2sem[mr] = sem;
        sem2root[sem] = mr;
        emit diplomaInfo( mr, sem);
    }

    function getRoot(uint256 sem) public view returns (uint256) {
        return sem2root[sem];
    }

    function getSem(uint256 mr) public view returns (uint256) {
        return root2sem[mr];
    }
}
