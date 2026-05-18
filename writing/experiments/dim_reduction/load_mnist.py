import numpy as np
import struct
from pathlib import Path

def load_mnist_images(file_path):
    """
    Load MNIST images from IDX3 format file
    
    Parameters:
    -----------
    file_path : str
        Path to the IDX3 file
        
    Returns:
    --------
    images : numpy.ndarray
        A 3D array with shape (num_images, height, width)
    """
    with open(file_path, 'rb') as f:
        # Read the magic number and dimensions
        magic, num_images, rows, cols = struct.unpack('>IIII', f.read(16))
        
        # Check magic number (2051 for images)
        if magic != 2051:
            raise ValueError(f'Invalid magic number {magic} in {file_path}')
        
        # Read the image data
        buffer = f.read(num_images * rows * cols)
        images = np.frombuffer(buffer, dtype=np.uint8)
        images = images.reshape(num_images, rows, cols)
        
        return images

def load_mnist_labels(file_path):
    """
    Load MNIST labels from IDX1 format file
    
    Parameters:
    -----------
    file_path : str
        Path to the IDX1 file
        
    Returns:
    --------
    labels : numpy.ndarray
        A 1D array with shape (num_labels,)
    """
    with open(file_path, 'rb') as f:
        # Read the magic number and dimensions
        magic, num_labels = struct.unpack('>II', f.read(8))
        
        # Check magic number (2049 for labels)
        if magic != 2049:
            raise ValueError(f'Invalid magic number {magic} in {file_path}')
        
        # Read the label data
        buffer = f.read(num_labels)
        labels = np.frombuffer(buffer, dtype=np.uint8)
        
        return labels

def load_mnist(dataset_path, dataset_type='train'):
    """
    Load MNIST dataset (images and labels)
    
    Parameters:
    -----------
    dataset_path : str
        Path to the MNIST dataset directory
    dataset_type : str
        'train' or 't10k' (test)
        
    Returns:
    --------
    images : numpy.ndarray
        A 3D array with shape (num_images, height, width)
    labels : numpy.ndarray
        A 1D array with shape (num_labels,)
    """
    dataset_path = Path(dataset_path)
    
    images_path = dataset_path / f'{dataset_type}-images.idx3-ubyte'
    labels_path = dataset_path / f'{dataset_type}-labels.idx1-ubyte'
    
    images = load_mnist_images(images_path)
    labels = load_mnist_labels(labels_path)
    
    return images, labels

# Example usage
if __name__ == "__main__":
    # Update this path to your MNIST dataset directory
    dataset_path = '/Users/edvintb/experiments/datasets/mnist'
    
    # Load training data
    train_images, train_labels = load_mnist(dataset_path, 'train')
    print(f"Training data: {train_images.shape} images, {train_labels.shape} labels")
    
    # Load test data
    test_images, test_labels = load_mnist(dataset_path, 't10k')
    print(f"Test data: {test_images.shape} images, {test_labels.shape} labels")
    
    # Display some statistics
    print(f"Image dimensions: {train_images[0].shape}")
    print(f"Label classes: {np.unique(train_labels)}")
    print(f"Sample label counts: {[(i, (train_labels == i).sum()) for i in range(10)]}")
