module.exports = [
    {
        "languageOptions": {
            "ecmaVersion": 2021,
            "sourceType": "commonjs",
            "globals": {
                "browser": true,
                "commonjs": true,
                "es2021": true,
                "node": true
            }
        },
        "rules": {
            "indent": [
                "error",
                4
            ],
            "linebreak-style": [
                "error",
                "unix"
            ],
            "quotes": [
                "error",
                "single"
            ],
            "semi": [
                "error",
                "always"
            ]
        }
    }
];
