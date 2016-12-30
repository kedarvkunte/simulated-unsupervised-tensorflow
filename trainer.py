from tqdm import tqdm

import tensorflow as tf
from tensorflow.contrib.framework.python.ops import arg_scope

from model import Model
from buffer import Buffer
import data.gaze_data as gaze_data
import data.hand_data as hand_data

class Trainer(object):
  def __init__(self, config, rng):
    self.task = config.task
    self.model_dir = config.model_dir

    self.K_d = config.K_d
    self.K_g = config.K_g
    self.initial_K_d = config.initial_K_d
    self.initial_K_g = config.initial_K_g
    self.checkpoint_secs = config.checkpoint_secs

    self.model = Model(config)
    self.history_buffer = Buffer(config)

    DataLoader = {
        'gaze': gaze_data.DataLoader,
        'hand': hand_data.DataLoader,
    }[config.data_set]
    self.data_loader = DataLoader(
        config.data_dir, config.batch_size, config.debug, rng=rng)

    self.summary_ops = {}
    self.summary_placeholders = {}

    self.saver = tf.train.Saver()
    self.summary_writer = tf.summary.FileWriter(self.model_dir)

  def train(self):
    self.model.build_optim()

    sv = tf.train.Supervisor(logdir=self.model_dir,
                             is_chief=True,
                             saver=self.saver,
                             summary_op=None,
                             summary_writer=self.summary_writer,
                             save_summaries_secs=300,
                             save_model_secs=self.checkpoint_secs,
                             global_step=self.model.global_step)

    config = tf.ConfigProto(allow_soft_placement=True)
    config.gpu_options.allow_growth=True

    sess = sv.prepare_or_wait_for_session(config=config)

    print("[*] Training starts...")

    for k in range(self.initial_K_g):
      res = self.model.train_refiner(
          sess, self.data_loader.next(), with_output)

    for k in range(self.initial_K_d):
      pass

    for step in range(self.max_step):
      for k in range(self.K_g):
        pass

      for k in range(self.K_d):
        pass

  def test(self):
    pass

  def _inject_summary(self, sess, tag_dict, step):
    feed_dict = {
        self.summary_placeholders[tag]: \
            value for tag, value in tag_dict.items()
    }
    summaries = sess.run(
        [self.summary_ops[tag] for tag in tag_dict.keys()], feed_dict)

    for summary in summaries:
      self.summary_writer.add_summary(summary, step)

  def _create_summary_op(self, tags):
    if type(tags) != list:
      tags = [tags]

    for tag in tags:
      self.summary_placeholders[tag] = \
          tf.placeholder('float32', None, name=tag.replace(' ', '_'))
      self.summary_ops[tag] = \
          tf.summary.scalar(tag, self.summary_placeholders[tag])
