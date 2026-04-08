# train a character-level baseball model for Noesis intuition module
# based on train_shakespeare_char.py - modified for baseball corpus

out_dir = 'out/noesis_checkpoint'
eval_interval = 500
eval_iters = 100
log_interval = 50

# Only save when val improves
always_save_checkpoint = True

wandb_log = False
wandb_project = 'noesis-baseball'
wandb_run_name = 'noesis-baseball-char'

dataset = 'baseball_char'
gradient_accumulation_steps = 1
batch_size = 64
block_size = 256  # context of up to 256 previous characters

# Small GPT model for fast training
n_layer = 4
n_head = 4
n_embd = 128
dropout = 0.2

learning_rate = 1e-3
max_iters = 5000
lr_decay_iters = 5000
min_lr = 1e-4
beta2 = 0.99

warmup_iters = 100

# CPU training
device = 'cpu'
compile = False
