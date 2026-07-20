const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './main.js', // Entry point for your application
  output: {
    filename: 'bundle.js', // Output bundle file
    path: path.resolve(__dirname, 'dist'), // Output directory
  },
  mode: 'development', // Development mode (use 'production' for production builds)
  devServer: {
    static: './dist', // Serve files from the 'dist' directory
    port: 5001, // Port for the development server
  },
  plugins: [
    // Automatically generate an HTML file that includes your bundled JS
    new HtmlWebpackPlugin({
      template: './index.html', // Use your existing index.html as a template
    }),
  ],
  module: {
    rules: [
      {
        test: /\.css$/, // Handle CSS files
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.js$/, // Transpile JavaScript files
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
      },
    ],
  },
};